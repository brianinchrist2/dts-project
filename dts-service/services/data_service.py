from __future__ import annotations

import logging
from typing import Optional

from mt5.connection import MT5Manager
from db.database import DatabaseManager
from db.repository import TickRepository
from models.schemas import QuoteItem, TickItem, SymbolInfo

logger = logging.getLogger(__name__)


class DataService:
    def __init__(self, mt5: MT5Manager, db: DatabaseManager) -> None:
        self._mt5 = mt5
        self._tick_repo = TickRepository(db)

    async def get_quotes(self, symbols: list[str]) -> list[QuoteItem]:
        quotes = []
        for sym in symbols:
            tick = await self._mt5.symbol_info_tick(sym)
            if tick is None:
                # 尝试选择品种并再次获取（解决品种未在市场报价中显示的问题）
                await self._mt5.execute("symbol_select", sym, True)
                tick = await self._mt5.symbol_info_tick(sym)
                
            if tick is None:
                continue
            quotes.append(QuoteItem(
                symbol=sym,
                bid=tick.bid,
                ask=tick.ask,
                time=int(tick.time),
            ))
        return quotes

    def get_cached_ticks(self, symbol: str, count: int = 20) -> list[TickItem]:
        rows = self._tick_repo.get_recent(symbol, count)
        return [TickItem(**r) for r in rows]

    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        info = await self._mt5.symbol_info(symbol)
        if info is None:
            return None
        return SymbolInfo(
            name=info.name,
            digits=info.digits,
            point=info.point,
            trade_contract_size=info.trade_contract_size,
            volume_min=info.volume_min,
            volume_max=info.volume_max,
            volume_step=info.volume_step,
        )
