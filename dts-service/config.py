from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    model_config = {"env_prefix": "DTS_"}

    # MT5 Bridge
    mt5_host: str = "127.0.0.1"
    mt5_port: int = 8001

    # Database
    db_path: str = "/home/gmag11/mt5-service/config/dts_main.db"

    # API auth
    api_key: str = "test-key"

    # Trading safety
    max_lot_size: float = 0.10
    allowed_server: str = "ICMarketsSC-Demo"
    trade_comment: str = "DMAS-API"

    # Symbol whitelist for tick collector
    symbols: List[str] = [
        "EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD",
    ]

    # Tick collector interval (seconds)
    tick_interval: float = 1.0

    # Kline aggregator interval (seconds)
    kline_interval: float = 60.0

    # Service
    version: str = "0.1.0"


settings = Settings()
