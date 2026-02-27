from fastapi import APIRouter, Depends

from dependencies import get_trading_service, require_api_key
from services.trading_service import TradingService
from models.schemas import (
    OrderRequest, OrderResult,
    PositionsResponse, PendingOrdersResponse,
    HistoryResponse,
)

router = APIRouter(
    prefix="/api/trading",
    tags=["trading"],
    dependencies=[Depends(require_api_key)],
)


@router.post("/orders", response_model=OrderResult)
async def place_order(
    req: OrderRequest,
    svc: TradingService = Depends(get_trading_service),
):
    return await svc.place_order(req)


@router.get("/positions", response_model=PositionsResponse)
async def get_positions(svc: TradingService = Depends(get_trading_service)):
    positions = await svc.get_positions()
    return PositionsResponse(positions=positions)


@router.delete("/positions/{ticket}", response_model=OrderResult)
async def close_position(
    ticket: int,
    svc: TradingService = Depends(get_trading_service),
):
    return await svc.close_position(ticket)


@router.get("/orders", response_model=PendingOrdersResponse)
async def get_pending_orders(svc: TradingService = Depends(get_trading_service)):
    orders = await svc.get_pending_orders()
    return PendingOrdersResponse(orders=orders)


@router.delete("/orders/{ticket}", response_model=OrderResult)
async def cancel_order(
    ticket: int,
    svc: TradingService = Depends(get_trading_service),
):
    return await svc.cancel_order(ticket)


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    days: int = 7,
    svc: TradingService = Depends(get_trading_service),
):
    deals = await svc.get_history(days)
    return HistoryResponse(deals=deals)
