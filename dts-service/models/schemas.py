from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Literal, Optional


# ── Data ────────────────────────────────────────────────────────────

class QuoteItem(BaseModel):
    symbol: str
    bid: float
    ask: float
    time: int

class QuotesResponse(BaseModel):
    quotes: list[QuoteItem]

class TickItem(BaseModel):
    symbol: str
    time: int
    bid: float
    ask: float
    last: Optional[float] = None
    volume: Optional[float] = None

class TicksResponse(BaseModel):
    symbol: str
    ticks: list[TickItem]

class KlineItem(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class KlinesResponse(BaseModel):
    symbol: str
    timeframe: str
    bars: list[KlineItem]

class SymbolInfo(BaseModel):
    name: str
    digits: int
    point: float
    trade_contract_size: float
    volume_min: float
    volume_max: float
    volume_step: float


# ── Trading ─────────────────────────────────────────────────────────

class OrderRequest(BaseModel):
    symbol: str
    order_type: Literal["BUY", "SELL", "BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP"]
    volume: float = Field(gt=0, le=0.10)
    price: Optional[float] = None  # required for pending orders
    stop_loss: float  # SAFE-02: required, no default
    take_profit: Optional[float] = None

class OrderResult(BaseModel):
    success: bool
    retcode: int
    ticket: Optional[int] = None
    message: str

class PositionItem(BaseModel):
    ticket: int
    symbol: str
    type: int
    volume: float
    price_open: float
    sl: float
    tp: float
    profit: float
    time: int

class PositionsResponse(BaseModel):
    positions: list[PositionItem]

class PendingOrderItem(BaseModel):
    ticket: int
    symbol: str
    type: int
    volume_current: float
    price_open: float
    sl: float
    tp: float
    time_setup: int

class PendingOrdersResponse(BaseModel):
    orders: list[PendingOrderItem]


# ── Account ─────────────────────────────────────────────────────────

class AccountInfo(BaseModel):
    login: int
    name: str
    server: str
    balance: float
    equity: float
    margin: float
    margin_free: float
    leverage: int
    currency: str

class DealItem(BaseModel):
    ticket: int
    time: int
    symbol: str
    type: int
    volume: float
    price: float
    profit: float
    commission: float
    swap: float

class HistoryResponse(BaseModel):
    deals: list[DealItem]


# ── System ──────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    mt5_connected: bool
    db_ok: bool

class VersionResponse(BaseModel):
    service_version: str
    mt5_version: Optional[str] = None
