import logging

from mt5.connection import MT5Manager
from mt5.constants import (
    ORDER_TYPE_BUY, ORDER_TYPE_SELL, ORDER_TYPE_BUY_LIMIT,
    ORDER_TYPE_SELL_LIMIT, ORDER_TYPE_BUY_STOP, ORDER_TYPE_SELL_STOP,
    TRADE_ACTION_DEAL, TRADE_ACTION_PENDING, TRADE_ACTION_REMOVE,
    TRADE_RETCODE_DONE, TRADE_RETCODE_PLACED,
    ORDER_FILLING_IOC, ORDER_TIME_GTC,
    POSITION_TYPE_BUY, POSITION_TYPE_SELL,
)
from db.database import DatabaseManager
from db.repository import TradeLogRepository
from models.schemas import OrderRequest, OrderResult
from services.safety import SafetyError, run_all_pre_trade_checks

logger = logging.getLogger(__name__)

_ORDER_TYPE_MAP = {
    "BUY": ORDER_TYPE_BUY,
    "SELL": ORDER_TYPE_SELL,
    "BUY_LIMIT": ORDER_TYPE_BUY_LIMIT,
    "SELL_LIMIT": ORDER_TYPE_SELL_LIMIT,
    "BUY_STOP": ORDER_TYPE_BUY_STOP,
    "SELL_STOP": ORDER_TYPE_SELL_STOP,
}


class TradingService:
    def __init__(self, mt5: MT5Manager, db: DatabaseManager) -> None:
        self._mt5 = mt5
        self._trade_log = TradeLogRepository(db)

    async def place_order(self, req: OrderRequest) -> OrderResult:
        # Fetch account to verify demo server (SAFE-01)
        account = await self._mt5.account_info()
        if account is None:
            return OrderResult(success=False, retcode=-1, message="Cannot retrieve account info")

        try:
            comment = run_all_pre_trade_checks(
                server=account.server,
                volume=req.volume,
                stop_loss=req.stop_loss,
            )
        except SafetyError as e:
            return OrderResult(success=False, retcode=-1, message=str(e))

        mt5_type = _ORDER_TYPE_MAP[req.order_type]
        is_market = req.order_type in ("BUY", "SELL")

        # For market orders, get current price
        price = req.price
        if is_market:
            tick = await self._mt5.symbol_info_tick(req.symbol)
            if tick is None:
                return OrderResult(success=False, retcode=-1, message=f"No tick for {req.symbol}")
            price = tick.ask if req.order_type == "BUY" else tick.bid
        elif price is None:
            return OrderResult(success=False, retcode=-1, message="Price required for pending orders")

        request = {
            "action": TRADE_ACTION_DEAL if is_market else TRADE_ACTION_PENDING,
            "symbol": req.symbol,
            "volume": req.volume,
            "type": mt5_type,
            "price": price,
            "sl": req.stop_loss,
            "tp": req.take_profit or 0.0,
            "type_filling": ORDER_FILLING_IOC,
            "type_time": ORDER_TIME_GTC,
            "comment": comment,  # SAFE-04: always overridden
        }

        result = await self._mt5.order_send(request)
        if result is None:
            err = await self._mt5.last_error()
            return OrderResult(success=False, retcode=-1, message=f"order_send failed: {err}")

        retcode = result.retcode
        ticket = getattr(result, "order", None) or getattr(result, "deal", None)
        success = retcode in (TRADE_RETCODE_DONE, TRADE_RETCODE_PLACED)

        # Log trade (SAFE-04 audit)
        self._trade_log.log_trade(
            ticket=ticket,
            symbol=req.symbol,
            order_type=req.order_type,
            volume=req.volume,
            price=price,
            sl=req.stop_loss,
            tp=req.take_profit or 0.0,
            retcode=retcode,
            comment=comment,
        )

        return OrderResult(
            success=success,
            retcode=retcode,
            ticket=ticket,
            message="OK" if success else f"MT5 retcode {retcode}",
        )

    async def get_positions(self) -> list[dict]:
        positions = await self._mt5.positions_get()
        if not positions:
            return []
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "type": p.type,
                "volume": p.volume,
                "price_open": p.price_open,
                "sl": p.sl,
                "tp": p.tp,
                "profit": p.profit,
                "time": int(p.time),
            }
            for p in positions
        ]

    async def close_position(self, ticket: int) -> OrderResult:
        positions = await self._mt5.positions_get(ticket=ticket)
        if not positions:
            return OrderResult(success=False, retcode=-1, message=f"Position {ticket} not found")

        pos = positions[0]
        close_type = ORDER_TYPE_SELL if pos.type == POSITION_TYPE_BUY else ORDER_TYPE_BUY
        tick = await self._mt5.symbol_info_tick(pos.symbol)
        if tick is None:
            return OrderResult(success=False, retcode=-1, message=f"No tick for {pos.symbol}")

        price = tick.bid if pos.type == POSITION_TYPE_BUY else tick.ask

        request = {
            "action": TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": ticket,
            "price": price,
            "type_filling": ORDER_FILLING_IOC,
            "comment": "DMAS-API",
        }

        result = await self._mt5.order_send(request)
        if result is None:
            err = await self._mt5.last_error()
            return OrderResult(success=False, retcode=-1, message=f"Close failed: {err}")

        success = result.retcode == TRADE_RETCODE_DONE
        return OrderResult(
            success=success,
            retcode=result.retcode,
            ticket=getattr(result, "order", None),
            message="Closed" if success else f"MT5 retcode {result.retcode}",
        )

    async def get_pending_orders(self) -> list[dict]:
        orders = await self._mt5.orders_get()
        if not orders:
            return []
        return [
            {
                "ticket": o.ticket,
                "symbol": o.symbol,
                "type": o.type,
                "volume_current": o.volume_current,
                "price_open": o.price_open,
                "sl": o.sl,
                "tp": o.tp,
                "time_setup": int(o.time_setup),
            }
            for o in orders
        ]

    async def cancel_order(self, ticket: int) -> OrderResult:
        request = {
            "action": TRADE_ACTION_REMOVE,
            "order": ticket,
        }
        result = await self._mt5.order_send(request)
        if result is None:
            err = await self._mt5.last_error()
            return OrderResult(success=False, retcode=-1, message=f"Cancel failed: {err}")

        success = result.retcode == TRADE_RETCODE_DONE
        return OrderResult(
            success=success,
            retcode=result.retcode,
            ticket=ticket,
            message="Cancelled" if success else f"MT5 retcode {result.retcode}",
        )

    async def get_history_deals(self, from_date: float, to_date: float) -> list[dict]:
        deals = await self._mt5.history_deals_get(from_date, to_date)
        if not deals:
            return []
        
        # Format for DealItem schema
        return [
            {
                "ticket": d.ticket,
                "time": int(d.time),
                "symbol": d.symbol,
                "type": d.type,
                "volume": d.volume,
                "price": d.price,
                "profit": d.profit,
                "commission": d.commission,
                "swap": d.swap,
            }
            for d in deals if d.symbol # Filter out non-trading deals like balance adjustments if needed, but schema asks for symbol
        ]

    async def get_history(self, days: int = 7) -> list[dict]:
        import time
        # 使用大幅前移的截止时间（+24小时），防止经纪商服务器时间领先于系统时间导致最后几笔交易被过滤
        to_date = time.time() + 86400
        from_date = time.time() - (days * 86400)
        
        deals = await self._mt5.history_deals_get(from_date, to_date)
        if not deals:
            return []
            
        return [
            {
                "ticket": d.ticket,
                "time": int(d.time),
                "symbol": d.symbol,
                "type": d.type,
                "volume": d.volume,
                "price": d.price,
                "profit": d.profit,
                "commission": d.commission,
                "swap": d.swap,
            }
            for d in deals
            if d.symbol  # 过滤掉账户存取款等非交易成交
        ]
