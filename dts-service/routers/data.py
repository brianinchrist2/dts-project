from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from config import settings
from dependencies import get_data_service, get_kline_service
from services.data_service import DataService
from services.kline_service import KlineService
from models.schemas import QuotesResponse, TicksResponse, KlinesResponse, SymbolInfo

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/quotes", response_model=QuotesResponse)
async def get_quotes(
    symbols: Optional[str] = Query(default=None),
    svc: DataService = Depends(get_data_service)
):
    if symbols:
        target_symbols = [s.strip() for s in symbols.split(",") if s.strip()]
    else:
        target_symbols = settings.symbols
        
    quotes = await svc.get_quotes(target_symbols)
    return QuotesResponse(quotes=quotes)


@router.get("/ticks/{symbol}", response_model=TicksResponse)
async def get_ticks(
    symbol: str,
    count: int = Query(default=20, ge=1, le=1000),
    svc: DataService = Depends(get_data_service),
):
    ticks = svc.get_cached_ticks(symbol, count)
    return TicksResponse(symbol=symbol, ticks=ticks)


@router.get("/klines/{symbol}", response_model=KlinesResponse)
async def get_klines(
    symbol: str,
    timeframe: str = Query(default="M1"),
    count: int = Query(default=100, ge=1, le=5000),
    svc: KlineService = Depends(get_kline_service),
):
    bars = await svc.get_klines(symbol, timeframe, count)
    return KlinesResponse(symbol=symbol, timeframe=timeframe, bars=bars)


@router.get("/symbols/{symbol}", response_model=SymbolInfo)
async def get_symbol_info(
    symbol: str,
    svc: DataService = Depends(get_data_service),
):
    info = await svc.get_symbol_info(symbol)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")
    return info
