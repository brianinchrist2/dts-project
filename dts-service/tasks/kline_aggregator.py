import asyncio
import logging

from config import settings
from mt5.connection import MT5Manager
from db.database import DatabaseManager
from services.kline_service import KlineService

logger = logging.getLogger(__name__)


class KlineAggregator:
    """Background task: periodically cache M1 klines to SQLite."""

    def __init__(self, mt5: MT5Manager, db: DatabaseManager) -> None:
        self._svc = KlineService(mt5, db)

    async def run(self) -> None:
        logger.info("KlineAggregator started (interval=%.0fs, symbols=%s)",
                     settings.kline_interval, settings.symbols)
        while True:
            try:
                await self._cache_all()
            except asyncio.CancelledError:
                logger.info("KlineAggregator stopped")
                return
            except Exception:
                logger.exception("KlineAggregator error")
            await asyncio.sleep(settings.kline_interval)

    async def _cache_all(self) -> None:
        if not self._svc._mt5.connected:
            return

        for symbol in settings.symbols:
            count = await self._svc.cache_m1(symbol)
            if count:
                logger.debug("Cached %d M1 bars for %s", count, symbol)
