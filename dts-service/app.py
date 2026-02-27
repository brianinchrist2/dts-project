import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from mt5.connection import MT5Manager
from db.database import DatabaseManager
from tasks.tick_collector import TickCollector
from tasks.kline_aggregator import KlineAggregator
from routers import system, data, trading, account

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── startup ──
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("DTS Service v%s starting", settings.version)

    # Init database
    db = DatabaseManager.get_instance()
    db.init_schema()

    # Connect to MT5
    mt5 = MT5Manager.get_instance()
    connected = await mt5.connect()
    if not connected:
        logger.warning("MT5 not available — data/trading endpoints will fail")

    # Start background tasks
    tick_collector = TickCollector(mt5, db)
    kline_aggregator = KlineAggregator(mt5, db)
    bg_tasks = [
        asyncio.create_task(tick_collector.run()),
        asyncio.create_task(kline_aggregator.run()),
    ]

    logger.info("DTS Service ready")
    yield

    # ── shutdown ──
    logger.info("DTS Service shutting down")
    for task in bg_tasks:
        task.cancel()
    await asyncio.gather(*bg_tasks, return_exceptions=True)
    await mt5.disconnect()
    db.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="DTS Service",
        description="MetaTrader 5 Docker Automation API",
        version=settings.version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    app.include_router(system.router)
    app.include_router(data.router)
    app.include_router(trading.router)
    app.include_router(account.router)
    return app
