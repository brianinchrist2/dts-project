from __future__ import annotations

import logging
import time
from typing import Optional

from mt5.connection import MT5Manager
from models.schemas import AccountInfo, DealItem

logger = logging.getLogger(__name__)


class AccountService:
    def __init__(self, mt5: MT5Manager) -> None:
        self._mt5 = mt5

    async def get_info(self) -> Optional[AccountInfo]:
        info = await self._mt5.account_info()
        if info is None:
            return None
        return AccountInfo(
            login=info.login,
            name=info.name,
            server=info.server,
            balance=info.balance,
            equity=info.equity,
            margin=info.margin,
            margin_free=info.margin_free,
            leverage=info.leverage,
            currency=info.currency,
        )

    async def get_history(self, days: int = 30) -> list[DealItem]:
        # 使用大幅前移的截止时间（+24小时），防止经纪商服务器时间领先于系统时间导致最后几笔交易被过滤
        to_date = time.time() + 86400 
        from_date = time.time() - (days * 86400)
        deals = await self._mt5.history_deals_get(from_date, to_date)
        if not deals:
            return []
        return [
            DealItem(
                ticket=d.ticket,
                time=int(d.time),
                symbol=d.symbol or "",
                type=d.type,
                volume=d.volume,
                price=d.price,
                profit=d.profit,
                commission=d.commission,
                swap=d.swap,
            )
            for d in deals
        ]
