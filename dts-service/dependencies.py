from fastapi import Depends, Header, HTTPException, status

from config import settings
from mt5.connection import MT5Manager
from db.database import DatabaseManager
from services.data_service import DataService
from services.kline_service import KlineService
from services.trading_service import TradingService
from services.account_service import AccountService


def get_mt5() -> MT5Manager:
    return MT5Manager.get_instance()


def get_db() -> DatabaseManager:
    return DatabaseManager.get_instance()


def get_data_service(
    mt5: MT5Manager = Depends(get_mt5),
    db: DatabaseManager = Depends(get_db),
) -> DataService:
    return DataService(mt5, db)


def get_kline_service(
    mt5: MT5Manager = Depends(get_mt5),
    db: DatabaseManager = Depends(get_db),
) -> KlineService:
    return KlineService(mt5, db)


def get_trading_service(
    mt5: MT5Manager = Depends(get_mt5),
    db: DatabaseManager = Depends(get_db),
) -> TradingService:
    return TradingService(mt5, db)


def get_account_service(
    mt5: MT5Manager = Depends(get_mt5),
) -> AccountService:
    return AccountService(mt5)


async def require_api_key(x_api_key: str = Header(...)) -> str:
    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return x_api_key
