import os
import sys
import tempfile

import pytest

# Add dts-service to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dts-service"))

# Override settings before any imports that use them
os.environ["DTS_DB_PATH"] = os.path.join(tempfile.gettempdir(), "dts_test.db")
os.environ["DTS_API_KEY"] = "test-key"
os.environ["DTS_MT5_HOST"] = "127.0.0.1"
os.environ["DTS_MT5_PORT"] = "8001"
os.environ["DTS_ALLOWED_SERVER"] = "ICMarketsSC-Demo"


class FakeTick:
    def __init__(self, bid=1.1000, ask=1.1002, time=1700000000, last=0, volume=0):
        self.bid = bid
        self.ask = ask
        self.time = time
        self.last = last
        self.volume = volume


class FakeAccount:
    def __init__(self, server="ICMarketsSC-Demo"):
        self.login = 12345
        self.name = "Test User"
        self.server = server
        self.balance = 10000.0
        self.equity = 10000.0
        self.margin = 0.0
        self.margin_free = 10000.0
        self.leverage = 100
        self.currency = "USD"


class FakeOrderResult:
    def __init__(self, retcode=10009, order=99999, deal=88888):
        self.retcode = retcode
        self.order = order
        self.deal = deal


class FakeSymbolInfo:
    def __init__(self, name="EURUSD"):
        self.name = name
        self.digits = 5
        self.point = 0.00001
        self.trade_contract_size = 100000.0
        self.volume_min = 0.01
        self.volume_max = 100.0
        self.volume_step = 0.01


class FakePosition:
    def __init__(self, ticket=100, symbol="EURUSD", pos_type=0):
        self.ticket = ticket
        self.symbol = symbol
        self.type = pos_type
        self.volume = 0.01
        self.price_open = 1.1000
        self.sl = 1.0900
        self.tp = 1.1100
        self.profit = 5.0
        self.time = 1700000000


class FakeMT5Manager:
    """Mock MT5Manager for unit tests (no real MT5 connection)."""

    def __init__(self):
        self._initialized = True
        self.account = FakeAccount()
        self.tick = FakeTick()
        self.order_result = FakeOrderResult()
        self.positions_list = [FakePosition()]

    @property
    def connected(self):
        return self._initialized

    async def connect(self):
        return True

    async def disconnect(self):
        self._initialized = False

    async def version(self):
        return (5, 0, 1)

    async def account_info(self):
        return self.account

    async def symbol_info(self, symbol):
        return FakeSymbolInfo(symbol)

    async def symbol_info_tick(self, symbol):
        return self.tick

    async def copy_rates_from_pos(self, symbol, timeframe, start, count):
        return None

    async def order_send(self, request):
        return self.order_result

    async def positions_get(self, **kwargs):
        if "ticket" in kwargs:
            return [p for p in self.positions_list if p.ticket == kwargs["ticket"]]
        return self.positions_list

    async def orders_get(self, **kwargs):
        return []

    async def history_deals_get(self, from_date, to_date):
        return []

    async def last_error(self):
        return (0, "No error")

    async def execute(self, func_name, *args, **kwargs):
        func = getattr(self, func_name, None)
        if func:
            return await func(*args, **kwargs)
        return None


@pytest.fixture
def fake_mt5():
    return FakeMT5Manager()


@pytest.fixture
def test_db():
    from db.database import DatabaseManager
    db_path = os.environ["DTS_DB_PATH"]
    db = DatabaseManager(db_path)
    db.init_schema()
    yield db
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)
    # Clean WAL/SHM files
    for ext in ("-wal", "-shm"):
        p = db_path + ext
        if os.path.exists(p):
            os.unlink(p)


@pytest.fixture
def app(fake_mt5, test_db):
    """Create a test FastAPI app with mocked MT5."""
    from mt5.connection import MT5Manager
    from db.database import DatabaseManager

    # Patch singletons
    MT5Manager._instance = fake_mt5
    DatabaseManager._instance = test_db

    from app import create_app
    test_app = create_app()
    # Remove lifespan for testing (we manage setup ourselves)
    test_app.router.lifespan_context = None

    yield test_app

    # Cleanup singletons
    MT5Manager._instance = None
    DatabaseManager._instance = None


@pytest.fixture
def client(app):
    from fastapi.testclient import TestClient
    return TestClient(app)
