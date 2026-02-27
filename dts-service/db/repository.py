from __future__ import annotations

from typing import Optional

from db.database import DatabaseManager


class TickRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def insert_ticks(self, ticks: list[tuple]) -> None:
        """Insert batch of (symbol, time, bid, ask, last, volume)."""
        self._db.executemany(
            "INSERT INTO ticks (symbol, time, bid, ask, last, volume) VALUES (?,?,?,?,?,?)",
            ticks,
        )
        self._db.commit()

    def get_recent(self, symbol: str, count: int = 20) -> list[dict]:
        rows = self._db.fetchall(
            "SELECT symbol, time, bid, ask, last, volume FROM ticks "
            "WHERE symbol = ? ORDER BY time DESC LIMIT ?",
            (symbol, count),
        )
        return [dict(r) for r in rows]


class KlineRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def upsert_m1(self, bars: list[tuple]) -> None:
        """Upsert batch of (symbol, time, open, high, low, close, volume)."""
        self._db.executemany(
            "INSERT OR REPLACE INTO klines_m1 (symbol, time, open, high, low, close, volume) "
            "VALUES (?,?,?,?,?,?,?)",
            bars,
        )
        self._db.commit()

    def get_m1(self, symbol: str, count: int = 100) -> list[dict]:
        rows = self._db.fetchall(
            "SELECT symbol, time, open, high, low, close, volume FROM klines_m1 "
            "WHERE symbol = ? ORDER BY time DESC LIMIT ?",
            (symbol, count),
        )
        return [dict(r) for r in rows]


class TradeLogRepository:
    def __init__(self, db: DatabaseManager) -> None:
        self._db = db

    def log_trade(self, ticket: Optional[int], symbol: str, order_type: str,
                  volume: float, price: float, sl: float, tp: float,
                  retcode: int, comment: str) -> None:
        self._db.execute(
            "INSERT INTO trade_log (ticket, symbol, order_type, volume, price, sl, tp, retcode, comment) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (ticket, symbol, order_type, volume, price, sl, tp, retcode, comment),
        )
        self._db.commit()
