import asyncio
import logging

from config import settings
from mt5.connection import MT5Manager
from db.database import DatabaseManager
from db.repository import TickRepository

logger = logging.getLogger(__name__)


class TickCollector:
    """Background task: poll latest ticks for whitelist symbols and cache to SQLite."""

    def __init__(self, mt5: MT5Manager, db: DatabaseManager) -> None:
        self._mt5 = mt5
        self._repo = TickRepository(db)

    async def run(self) -> None:
        logger.info("TickCollector started (interval=%.1fs, symbols=%s)",
                     settings.tick_interval, settings.symbols)
        while True:
            try:
                await self._poll()
            except asyncio.CancelledError:
                logger.info("TickCollector stopped")
                return
            except Exception:
                logger.exception("TickCollector error")
            await asyncio.sleep(settings.tick_interval)

    async def _poll(self) -> None:
        if not self._mt5.connected:
            return

        batch: list[tuple] = []
        for symbol in settings.symbols:
            tick = await self._mt5.symbol_info_tick(symbol)
            if tick is None:
                continue
            batch.append((
                symbol,
                int(tick.time),
                tick.bid,
                tick.ask,
                getattr(tick, "last", None),
                getattr(tick, "volume", None),
            ))

        if batch:
            self._repo.insert_ticks(batch)
            logger.debug("Collected %d ticks", len(batch))
