import logging

from mt5.connection import MT5Manager
from mt5.constants import TIMEFRAME_M1, TIMEFRAME_MAP
from db.database import DatabaseManager
from db.repository import KlineRepository
from models.schemas import KlineItem

logger = logging.getLogger(__name__)

# Aggregation ratios: how many M1 bars make one bar of each timeframe
_AGG_MINUTES = {
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


def _aggregate_m1(bars: list[KlineItem], period: int) -> list[KlineItem]:
    """Aggregate M1 KlineItems into a higher timeframe."""
    if not bars:
        return []

    # Sort ascending by time for grouping
    sorted_bars = sorted(bars, key=lambda b: b.time)
    result: list[KlineItem] = []
    chunk: list[KlineItem] = []

    for bar in sorted_bars:
        if not chunk:
            chunk.append(bar)
            continue
        # Group by rounding time down to nearest `period` minutes
        group_start = chunk[0].time - (chunk[0].time % (period * 60))
        bar_group = bar.time - (bar.time % (period * 60))
        if bar_group == group_start:
            chunk.append(bar)
        else:
            result.append(_merge_chunk(chunk))
            chunk = [bar]

    if chunk:
        result.append(_merge_chunk(chunk))

    return result


def _merge_chunk(chunk: list[KlineItem]) -> KlineItem:
    return KlineItem(
        time=chunk[0].time,
        open=chunk[0].open,
        high=max(b.high for b in chunk),
        low=min(b.low for b in chunk),
        close=chunk[-1].close,
        volume=sum(b.volume for b in chunk),
    )


class KlineService:
    def __init__(self, mt5: MT5Manager, db: DatabaseManager) -> None:
        self._mt5 = mt5
        self._kline_repo = KlineRepository(db)

    async def get_klines(self, symbol: str, timeframe: str, count: int) -> list[KlineItem]:
        """Return OHLCV bars. M1 from MT5 directly; higher TFs aggregated from M1."""
        if timeframe == "M1":
            return await self._fetch_m1_from_mt5(symbol, count)

        period = _AGG_MINUTES.get(timeframe)
        if period is None:
            return []

        # Fetch enough M1 bars to produce `count` higher-TF bars
        m1_needed = count * period
        m1_bars = await self._fetch_m1_from_mt5(symbol, m1_needed)
        aggregated = _aggregate_m1(m1_bars, period)

        # Return latest `count` bars, descending
        return sorted(aggregated, key=lambda b: b.time, reverse=True)[:count]

    async def _fetch_m1_from_mt5(self, symbol: str, count: int) -> list[KlineItem]:
        rates = await self._mt5.copy_rates_from_pos(symbol, TIMEFRAME_M1, 0, count)
        if rates is None:
            # Fallback to DB cache
            rows = self._kline_repo.get_m1(symbol, count)
            return [KlineItem(**r) for r in rows]

        items = []
        for r in rates:
            items.append(KlineItem(
                time=int(r[0]) if not hasattr(r, "time") else int(r.time),
                open=r[1] if not hasattr(r, "open") else r.open,
                high=r[2] if not hasattr(r, "high") else r.high,
                low=r[3] if not hasattr(r, "low") else r.low,
                close=r[4] if not hasattr(r, "close") else r.close,
                volume=float(r[5] if not hasattr(r, "tick_volume") else r.tick_volume),
            ))
        return items

    async def cache_m1(self, symbol: str, count: int = 200) -> int:
        """Fetch M1 from MT5 and cache to SQLite. Returns number of bars cached."""
        bars = await self._fetch_m1_from_mt5(symbol, count)
        if not bars:
            return 0
        tuples = [(symbol, b.time, b.open, b.high, b.low, b.close, b.volume) for b in bars]
        self._kline_repo.upsert_m1(tuples)
        return len(tuples)
