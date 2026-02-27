from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from mt5linux import MetaTrader5

from config import settings

logger = logging.getLogger(__name__)


class MT5Manager:
    """Singleton async wrapper around mt5linux (blocking TCP calls)."""

    _instance: Optional[MT5Manager] = None

    def __init__(self) -> None:
        self._mt5: Optional[MetaTrader5] = None
        self._initialized = False

    @classmethod
    def get_instance(cls) -> "MT5Manager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -- lifecycle --------------------------------------------------------

    async def connect(self) -> bool:
        self._mt5 = MetaTrader5(settings.mt5_host, settings.mt5_port)
        ok = await asyncio.to_thread(self._mt5.initialize)
        self._initialized = bool(ok)
        if self._initialized:
            logger.info("MT5 connected to %s:%s", settings.mt5_host, settings.mt5_port)
        else:
            logger.error("MT5 initialize failed: %s", await self.last_error())
        return self._initialized

    async def disconnect(self) -> None:
        if self._mt5:
            await asyncio.to_thread(self._mt5.shutdown)
            self._initialized = False
            logger.info("MT5 disconnected")

    @property
    def connected(self) -> bool:
        return self._initialized

    # -- generic executor -------------------------------------------------

    async def execute(self, func_name: str, *args: Any, **kwargs: Any) -> Any:
        """Run any mt5.<func_name>(*args, **kwargs) off the event loop."""
        if not self._mt5:
            raise RuntimeError("MT5 not connected — call connect() first")
        func = getattr(self._mt5, func_name)
        return await asyncio.to_thread(func, *args, **kwargs)

    # -- convenience shortcuts --------------------------------------------

    async def last_error(self) -> Any:
        return await self.execute("last_error")

    async def version(self) -> Any:
        return await self.execute("version")

    async def account_info(self) -> Any:
        return await self.execute("account_info")

    async def symbol_info(self, symbol: str) -> Any:
        return await self.execute("symbol_info", symbol)

    async def symbol_info_tick(self, symbol: str) -> Any:
        return await self.execute("symbol_info_tick", symbol)

    async def symbols_get(self) -> Any:
        return await self.execute("symbols_get")

    async def copy_rates_from_pos(self, symbol: str, timeframe: int, start_pos: int, count: int) -> Any:
        return await self.execute("copy_rates_from_pos", symbol, timeframe, start_pos, count)

    async def copy_ticks_from_pos(self, symbol: str, start_pos: int, count: int) -> Any:
        return await self.execute("copy_ticks_from_pos", symbol, start_pos, count)

    async def order_send(self, request: dict) -> Any:
        return await self.execute("order_send", request)

    async def positions_get(self, **kwargs: Any) -> Any:
        return await self.execute("positions_get", **kwargs)

    async def orders_get(self, **kwargs: Any) -> Any:
        return await self.execute("orders_get", **kwargs)

    async def history_deals_get(self, from_date: float, to_date: float) -> Any:
        return await self.execute("history_deals_get", from_date, to_date)
