# DTS Service Specification

**Version**: v1.0.0
**Last Updated**: 2026-02-26
**Purpose**: Technical specification for the DTS (MetaTrader 5 Docker Automation) service layer

---

## 1. Overview

### 1.1 Service Definition
DTS Service is a FastAPI-based REST API that provides standardized interfaces for algorithmic trading systems to interact with MetaTrader 5 (MT5). It acts as the middleware layer between external trading strategies and a containerized MT5 terminal, managing data collection, trade execution, and account state synchronization.

### 1.2 Core Responsibilities
- **Data Collection**: Collect and persist tick data, OHLCV candles, and market quotes
- **Trade Execution**: Submit, modify, and cancel orders with strict risk controls
- **Account Monitoring**: Provide real-time account balance, equity, and margin information
- **Technical Indicators**: Calculate and serve technical indicators (RSI, EMA, etc.)
- **Audit Trail**: Log all API operations for compliance and debugging

### 1.3 Technology Stack
- **Framework**: FastAPI (async Python web framework)
- **Server**: Uvicorn (ASGI server)
- **Database**: SQLite3 (persistent data storage)
- **MT5 Bridge**: `mt5linux` library over TCP port 8001
- **Python Version**: 3.9+

---

## 2. Architecture

### 2.1 Service Structure

```
dts-service/
├── main.py                  # Entry point (uvicorn startup)
├── app.py                   # FastAPI app factory
├── config.py                # Configuration management
├── dependencies.py          # Dependency injection
├── mt5/
│   ├── connection.py        # MT5 bridge initialization and connection
│   └── constants.py         # MT5-specific constants and symbols
├── db/
│   ├── database.py          # SQLite connection and setup
│   └── repository.py        # Data access layer (queries)
├── models/
│   └── schemas.py           # Pydantic data models for API/database
├── services/
│   ├── data_service.py      # Market data operations
│   ├── trading_service.py   # Order execution and management
│   ├── account_service.py   # Account info and balance tracking
│   ├── kline_service.py     # OHLCV aggregation and synthesis
│   └── safety.py            # Risk controls and validation
├── routers/
│   ├── system.py            # Health checks, status endpoints
│   ├── data.py              # Market data endpoints (quotes, ticks, klines)
│   ├── trading.py           # Order management endpoints
│   └── account.py           # Account info endpoints
└── tasks/
    ├── tick_collector.py    # Background task: collect ticks
    └── kline_aggregator.py  # Background task: aggregate M1 → M5/H1/D1
```

### 2.2 Communication Flow

```
External Trading System
         ↓
    FastAPI Router
         ↓
    Service Layer (business logic)
         ↓
    Data Access Layer (database)
         ↓
    MT5 Bridge (mt5linux)
         ↓
    MT5 Docker Container (Wine)
```

### 2.3 Component Interactions

| Component | Responsibility | Dependencies |
|-----------|---|---|
| **mt5/connection.py** | Initialize and maintain MT5 bridge connection | `mt5linux` |
| **db/database.py** | Create/manage SQLite database | `sqlite3` |
| **db/repository.py** | Query and insert data (ticks, klines) | `database.py` |
| **services/data_service.py** | Fetch market data from MT5 | `mt5/connection.py`, `db/repository.py` |
| **services/trading_service.py** | Execute trades, manage orders | `mt5/connection.py`, `services/safety.py` |
| **services/account_service.py** | Query account state | `mt5/connection.py` |
| **services/kline_service.py** | Synthesize timeframe aggregations | `db/repository.py` |
| **services/safety.py** | Validate trades, enforce risk rules | (standalone) |
| **routers/* ** | HTTP endpoints | All services |
| **tasks/* ** | Background jobs (tick collection, aggregation) | All services, database |

---

## 3. API Endpoints

### 3.1 System Endpoints (`/api/system`)

#### GET `/api/system/health`
**Purpose**: Check service and MT5 bridge health
**Response**:
```json
{
  "status": "healthy",
  "mt5_connected": true,
  "database_status": "ok",
  "timestamp": "2026-02-26T12:00:00Z"
}
```

#### GET `/api/system/version`
**Purpose**: Get MT5 terminal version and API version
**Response**:
```json
{
  "api_version": "1.0.0",
  "mt5_version": "5.0.5000",
  "build_date": "2026-02-01"
}
```

---

### 3.2 Data Endpoints (`/api/data`)

#### GET `/api/data/quotes`
**Purpose**: Get latest Bid/Ask quotes for requested symbols
**Query Parameters**: `symbols` (comma-separated list)
**Response**:
```json
[
  {
    "symbol": "EURUSD",
    "bid": 1.0950,
    "ask": 1.0952,
    "timestamp": 1708957200000
  }
]
```

#### GET `/api/data/ticks`
**Purpose**: Get recent ticks for a symbol (default: last 20)
**Query Parameters**: `symbol`, `limit` (optional, max 100)
**Response**:
```json
{
  "symbol": "EURUSD",
  "ticks": [
    {
      "time": 1708957200000,
      "bid": 1.0950,
      "ask": 1.0952
    }
  ]
}
```

#### GET `/api/data/klines/{symbol}`
**Purpose**: Get OHLCV candles for a symbol and timeframe with smart multi-timeframe aggregation
**Path Parameters**: `symbol` (e.g., EURUSD, BTCUSD)
**Query Parameters**:
- `timeframe` (M1, M5, M15, M30, H1, H4, D1) - default: M1
- `count` (1-5000) - number of candles to return, default: 100
**Response**:
```json
{
  "symbol": "EURUSD",
  "timeframe": "H1",
  "bars": [
    {
      "time": 1772078400,
      "open": 1.18274,
      "high": 1.18289,
      "low": 1.18132,
      "close": 1.18172,
      "volume": 1889.0
    },
    {
      "time": 1772074800,
      "open": 1.18191,
      "high": 1.18289,
      "low": 1.18179,
      "close": 1.18274,
      "volume": 2561.0
    }
  ]
}
```

**Implementation Details**:
- **M1 Candles**: Fetched directly from MT5 via `copy_rates_from_pos()`
- **Higher Timeframes**: Intelligently aggregated from M1 candles:
  - M5: Groups 5 M1 bars
  - M15: Groups 15 M1 bars
  - M30: Groups 30 M1 bars
  - H1: Groups 60 M1 bars
  - H4: Groups 240 M1 bars
  - D1: Groups 1440 M1 bars (full day)
- **OHLCV Calculation**:
  - Open: First bar's opening price
  - High: Maximum price across all grouped bars
  - Low: Minimum price across all grouped bars
  - Close: Last bar's closing price
  - Volume: Sum of volumes across all grouped bars
- **Persistence**: Background task caches M1 data to SQLite every 60 seconds as fallback

#### GET `/api/data/indicators`
**Purpose**: Calculate technical indicators
**Query Parameters**: `symbol`, `timeframe`, `indicator` (RSI, EMA, SMA, MACD), `period` (optional)
**Response**:
```json
{
  "symbol": "EURUSD",
  "indicator": "RSI",
  "period": 14,
  "value": 65.23,
  "timestamp": 1708957200000
}
```

---

### 3.3 Trading Endpoints (`/api/trading`)

#### POST `/api/trading/orders`
**Purpose**: Submit a new market or limit order
**Request Body**:
```json
{
  "symbol": "EURUSD",
  "action": "buy",
  "volume": 0.01,
  "order_type": "market",
  "stop_loss": 1.0900,
  "take_profit": 1.1000,
  "comment": "DMAS-API"
}
```
**Response**:
```json
{
  "order_id": 12345,
  "symbol": "EURUSD",
  "status": "executed",
  "entry_price": 1.0950,
  "timestamp": 1708957200000
}
```

#### GET `/api/trading/orders`
**Purpose**: Get all open orders
**Response**:
```json
[
  {
    "order_id": 12345,
    "symbol": "EURUSD",
    "volume": 0.01,
    "entry_price": 1.0950,
    "stop_loss": 1.0900,
    "take_profit": 1.1000,
    "status": "open"
  }
]
```

#### GET `/api/trading/orders/{order_id}`
**Purpose**: Get a specific order details
**Response**:
```json
{
  "order_id": 12345,
  "symbol": "EURUSD",
  "volume": 0.01,
  "entry_price": 1.0950,
  "current_price": 1.0955,
  "floating_pnl": 5.00,
  "status": "open",
  "opened_at": 1708957200000
}
```

#### PUT `/api/trading/orders/{order_id}`
**Purpose**: Modify an order (SL/TP/volume)
**Request Body**:
```json
{
  "stop_loss": 1.0905,
  "take_profit": 1.1010
}
```
**Response**:
```json
{
  "order_id": 12345,
  "status": "updated",
  "stop_loss": 1.0905,
  "take_profit": 1.1010
}
```

#### DELETE `/api/trading/orders/{order_id}`
**Purpose**: Close/cancel an order
**Response**:
```json
{
  "order_id": 12345,
  "status": "closed",
  "close_price": 1.0960,
  "realized_pnl": 10.00,
  "closed_at": 1708957201000
}
```

#### GET `/api/trading/history`
**Purpose**: Get closed trades (history)
**Query Parameters**: `symbol` (optional), `limit` (default 100)
**Response**:
```json
[
  {
    "order_id": 12344,
    "symbol": "EURUSD",
    "volume": 0.01,
    "entry_price": 1.0940,
    "close_price": 1.0960,
    "realized_pnl": 20.00,
    "opened_at": 1708950000000,
    "closed_at": 1708957200000
  }
]
```

---

### 3.4 Account Endpoints (`/api/account`)

#### GET `/api/account/info`
**Purpose**: Get account summary (balance, equity, margin)
**Response**:
```json
{
  "account_id": "ICMarketsSC-Demo-12345",
  "balance": 10000.00,
  "equity": 10050.00,
  "margin_used": 100.00,
  "margin_free": 9900.00,
  "margin_level": 100.50,
  "floating_pnl": 50.00
}
```

#### GET `/api/account/positions`
**Purpose**: Get all open positions
**Response**:
```json
[
  {
    "symbol": "EURUSD",
    "volume": 0.01,
    "entry_price": 1.0950,
    "current_price": 1.0955,
    "floating_pnl": 5.00,
    "commission": 1.00
  }
]
```

#### GET `/api/account/symbols`
**Purpose**: Get available trading symbols
**Response**:
```json
[
  {
    "symbol": "EURUSD",
    "description": "Euro vs US Dollar",
    "digits": 5,
    "point": 0.00001,
    "min_volume": 0.01,
    "max_volume": 100.0,
    "volume_step": 0.01
  }
]
```

---

## 4. Data Models

### 4.1 Tick Model
```python
class Tick(BaseModel):
    symbol: str
    time: int              # Unix timestamp in milliseconds
    bid: float
    ask: float
    volume: Optional[int]  # Volume in lots
```

### 4.2 Kline Model (OHLCV)
```python
class Kline(BaseModel):
    symbol: str
    timeframe: str         # M1, M5, H1, D1, W1, MN1
    time: int              # Open time (Unix ms)
    open: float
    high: float
    low: float
    close: float
    volume: int            # Volume in ticks
```

### 4.3 Order Model
```python
class Order(BaseModel):
    order_id: int
    symbol: str
    volume: float          # Position size in lots
    action: str            # buy or sell
    order_type: str        # market, limit, stop
    entry_price: float
    stop_loss: float       # Required for risk management
    take_profit: Optional[float]
    status: str            # open, closed, cancelled, pending
    opened_at: int         # Unix timestamp (ms)
    closed_at: Optional[int]
    realized_pnl: Optional[float]
    comment: str           # Audit trail (e.g., "DMAS-API")
```

### 4.4 Account Model
```python
class AccountInfo(BaseModel):
    account_id: str
    balance: float         # Account balance
    equity: float          # Current equity (balance + floating PnL)
    margin_used: float     # Margin in use
    margin_free: float     # Available margin
    margin_level: float    # Equity / Margin Used * 100
    floating_pnl: float    # Unrealized P&L from open positions
    currency: str          # Account currency (e.g., "USD")
```

### 4.5 Quote Model
```python
class Quote(BaseModel):
    symbol: str
    bid: float
    ask: float
    volume: int            # Bid/Ask volume
    timestamp: int         # Unix timestamp (ms)
```

---

## 5. Database Schema

### 5.1 Tables

#### `ticks` Table
Stores raw tick data for backtesting and analysis.

```sql
CREATE TABLE ticks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  time INTEGER NOT NULL,         -- Unix timestamp (ms)
  bid REAL NOT NULL,
  ask REAL NOT NULL,
  volume INTEGER,
  created_at INTEGER DEFAULT (CAST(julianday('now') * 86400000 AS INTEGER))
);

CREATE INDEX idx_ticks_symbol_time ON ticks(symbol, time DESC);
```

#### `klines` Table
Stores aggregated OHLCV data for multiple timeframes.

```sql
CREATE TABLE klines (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,       -- M1, M5, H1, D1, W1, MN1
  time INTEGER NOT NULL,         -- Candle open time (Unix ms)
  open REAL NOT NULL,
  high REAL NOT NULL,
  low REAL NOT NULL,
  close REAL NOT NULL,
  volume INTEGER NOT NULL,
  created_at INTEGER DEFAULT (CAST(julianday('now') * 86400000 AS INTEGER))
);

CREATE UNIQUE INDEX idx_klines_symbol_tf_time ON klines(symbol, timeframe, time);
```

#### `orders` Table
Stores trade history and execution records.

```sql
CREATE TABLE orders (
  order_id INTEGER PRIMARY KEY,
  symbol TEXT NOT NULL,
  volume REAL NOT NULL,
  action TEXT NOT NULL,           -- buy, sell
  order_type TEXT NOT NULL,       -- market, limit, stop
  entry_price REAL NOT NULL,
  stop_loss REAL,
  take_profit REAL,
  status TEXT NOT NULL,           -- open, closed, cancelled, pending
  opened_at INTEGER NOT NULL,
  closed_at INTEGER,
  realized_pnl REAL,
  comment TEXT,                   -- Audit trail
  created_at INTEGER DEFAULT (CAST(julianday('now') * 86400000 AS INTEGER))
);

CREATE INDEX idx_orders_symbol_status ON orders(symbol, status);
CREATE INDEX idx_orders_opened_at ON orders(opened_at DESC);
```

#### `account_snapshots` Table (Optional)
Historical snapshots of account state for reporting.

```sql
CREATE TABLE account_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  balance REAL NOT NULL,
  equity REAL NOT NULL,
  margin_used REAL NOT NULL,
  margin_free REAL NOT NULL,
  floating_pnl REAL NOT NULL,
  timestamp INTEGER NOT NULL,
  created_at INTEGER DEFAULT (CAST(julianday('now') * 86400000 AS INTEGER))
);

CREATE INDEX idx_snapshots_timestamp ON account_snapshots(timestamp DESC);
```

### 5.2 Data Retention Policies

| Table | Retention | Purpose |
|-------|-----------|---------|
| `ticks` | 30 days | Real-time analysis, backtesting |
| `klines` | Unlimited | Historical price data |
| `orders` | Unlimited | Audit trail, strategy analysis |
| `account_snapshots` | 90 days | Performance reporting |

---

## 6. Configuration

### 6.1 Configuration File (`config.py`)

```python
# MT5 Connection
MT5_HOST = "127.0.0.1"         # Local Docker or "152.32.201.243" for remote
MT5_PORT = 8001                 # Standard MT5 bridge port
MT5_TIMEOUT = 30                # seconds

# Database
DB_PATH = "./data/dts_main.db"  # SQLite database file path
DB_TIMEOUT = 10                 # seconds

# API Server
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True               # Hot reload during development

# Trading Rules (Safety)
DEMO_ACCOUNT_ONLY = True        # SAFE-01: Force demo account
ENFORCE_STOP_LOSS = True        # SAFE-02: Require stop loss on all trades
MAX_LOT_SIZE = 0.01             # SAFE-03: Max test trade size
SAFE_COMMENT = "DMAS-API"       # SAFE-04: Audit trail comment

# Features
TICK_COLLECTOR_ENABLED = True
KLINE_AGGREGATOR_ENABLED = True
SYMBOLS_WHITELIST = ["EURUSD", "GBPUSD", "USDJPY"]  # Optional whitelist
```

### 6.2 Environment Variables

```bash
# MT5 Connection
export MT5_HOST="127.0.0.1"
export MT5_PORT="8001"

# Database
export DB_PATH="/home/gmag11/mt5-service/config/dts_main.db"

# API
export API_PORT="8000"

# Trading
export ENFORCE_STOP_LOSS="true"
export DEMO_ACCOUNT_ONLY="true"
```

---

## 7. Deployment and Running

### 7.1 Prerequisites

1. **Docker running** with MT5 container: `ghcr.io/gmag11/metatrader5-docker`
2. **Python 3.9+** installed
3. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

### 7.2 Starting the Service

```bash
# Development mode (with auto-reload)
python dts-service/main.py

# Production mode (with gunicorn/supervisor)
uvicorn dts-service.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7.3 Verification

```bash
# Check service health
curl http://localhost:8000/api/system/health

# Get MT5 version
curl http://localhost:8000/api/system/version

# Get quotes
curl "http://localhost:8000/api/data/quotes?symbols=EURUSD,GBPUSD"
```

### 7.4 Docker Compose Example

```yaml
version: "3.8"

services:
  dts-service:
    image: python:3.9-slim
    working_dir: /app
    volumes:
      - ./dts-service:/app/dts-service
      - ./requirements.txt:/app/requirements.txt
    ports:
      - "8000:8000"
    environment:
      - MT5_HOST=mt5-bridge
      - MT5_PORT=8001
      - DB_PATH=/data/dts_main.db
    command: >
      sh -c "pip install -r requirements.txt &&
             python dts-service/main.py"
    depends_on:
      - mt5-bridge

  mt5-bridge:
    image: ghcr.io/gmag11/metatrader5-docker:latest
    ports:
      - "8001:8001"
    volumes:
      - mt5-data:/home/gmag11/mt5-service/config
    environment:
      - WINE_CPU_TOPOLOGY=4:2
      - DISPLAY=:99

volumes:
  mt5-data:
```

---

## 8. Safety Rules (Non-Negotiable)

All trading operations must adhere to these hard constraints:

### [SAFE-01] Demo Accounts Only
- **Rule**: All trades must target `ICMarketsSC-Demo` server unless explicitly authorized by Brian
- **Enforcement**: Configuration enforced at startup
- **Violation Consequence**: Trades rejected with HTTP 403 error

### [SAFE-02] Stop Loss Enforcement
- **Rule**: Every open position must include a `stop_loss` parameter
- **Enforcement**: Validation in `services/safety.py:validate_order()`
- **Violation Consequence**: Orders rejected with HTTP 400 error

### [SAFE-03] Lot Size Limits
- **Rule**: Test trades limited to **0.01 lots** maximum per position
- **Enforcement**: Configuration checked in `services/safety.py:validate_volume()`
- **Violation Consequence**: Orders reduced to max allowed size with warning

### [SAFE-04] API Logging
- **Rule**: All executed trades must include `comment: "DMAS-API"` for audit trail
- **Enforcement**: Automatically appended if not provided
- **Verification**: Query `/api/trading/history` and verify comment field

---

## 9. Background Tasks

### 9.1 Tick Collector (`tasks/tick_collector.py`)

**Purpose**: Continuously collect and persist tick data
**Schedule**: Runs on background thread
**Interval**: ~100ms per symbol (configurable)
**Symbols**: All symbols in whitelist
**Database**: Inserts into `ticks` table

```python
# Example output to database
INSERT INTO ticks (symbol, time, bid, ask, volume)
VALUES ('EURUSD', 1708957200000, 1.0950, 1.0952, 150000);
```

### 9.2 Kline Aggregator (`tasks/kline_aggregator.py`)

**Purpose**: Cache M1 candles to SQLite for data persistence and MT5 fallback
**Schedule**: Runs on background thread
**Interval**: Every 60 seconds
**Algorithm**: Fetches latest M1 bars from MT5 and caches to database
**Database**: Stores in `klines` table for M1 data persistence
**Fallback**: When MT5 is temporarily unavailable, API uses cached M1 data to serve klines requests

**Flow**:
1. Background task runs every 60s
2. Fetches latest 200 M1 candles from MT5 for each whitelisted symbol
3. Stores/updates candles in SQLite `klines` table
4. When API receives klines request:
   - Fetches M1 data from MT5 (preferred)
   - If MT5 fails, retrieves cached M1 from database
   - Aggregates M1 into requested timeframe (M5, H1, D1, etc.) on-the-fly
5. Returns aggregated OHLCV data to client

**Benefits**:
- Real-time data from MT5 when available
- Graceful degradation if MT5 temporarily unavailable
- Efficient aggregation without pre-computing all timeframes
- Reduced database load (only M1 cached, higher TFs computed dynamically)

---

## 10. Error Handling

### 10.1 HTTP Status Codes

| Code | Scenario | Example |
|------|----------|---------|
| 200 | Success | Trade executed, quote retrieved |
| 400 | Validation Error | Missing stop loss, invalid lot size |
| 403 | Safety Violation | Live account access blocked, position exceeds limit |
| 404 | Not Found | Order ID doesn't exist, symbol not available |
| 500 | Server Error | MT5 bridge disconnected, database error |
| 503 | Service Unavailable | MT5 initializing, bridge reconnecting |

### 10.2 Error Response Format

```json
{
  "error": "Validation Error",
  "detail": "Stop loss required for new positions",
  "code": "SAFE_02_VIOLATION",
  "timestamp": "2026-02-26T12:00:00Z"
}
```

---

## 11. Testing

### 11.1 Test Structure

Tests are located in `/dts-test/` and organized by module:

```bash
dts-test/
├── test_connection.py      # MT5 bridge connectivity
├── test_data_api.py        # Data endpoints (quotes, ticks, klines)
├── test_trading_api.py     # Order execution endpoints
├── test_models.py          # Data model validation
├── test_safety.py          # Safety rule enforcement
└── conftest.py             # Shared fixtures
```

### 11.2 Running Tests

```bash
# All tests
python -m unittest discover -s dts-test -p "test_*.py" -v

# Specific test file
python -m unittest dts-test.test_safety -v

# Single test case
python -m unittest dts-test.test_trading_api.TestOrderExecution.test_market_order -v
```

### 11.3 Test Coverage

Target coverage: **>= 80%** of critical paths (safety, data persistence, order execution)

---

## 12. Monitoring and Debugging

### 12.1 Logging

All modules use Python's `logging` module:

```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Order {order_id} executed at {entry_price}")
logger.error(f"MT5 connection failed: {error}", exc_info=True)
```

**Log Levels**:
- `DEBUG`: Detailed tick/kline data, connection events
- `INFO`: Trade executions, API requests, service startup
- `WARNING`: Retries, connection slowdowns, non-critical failures
- `ERROR`: Order rejections, database errors, bridge disconnections
- `CRITICAL`: Service shutdown, data loss, safety violations

### 12.2 Health Checks

**Endpoint**: `GET /api/system/health`
**Response Indicators**:
- `mt5_connected`: MT5 bridge is reachable
- `database_status`: SQLite database is writable
- `status`: Overall service health (healthy/degraded/offline)

### 12.3 Debugging MT5 Connection Issues

```bash
# Test MT5 bridge connectivity
python dts-demo/mt5_conn_demo.py

# Check bridge port availability
netstat -an | grep 8001

# Restart MT5 bridge (if applicable)
bash scripts/restart_mt5_bridge.sh
```

---

## 13. Development Guidelines

### 13.1 Code Style

- **Format**: PEP 8 (use `black` or `flake8`)
- **Type Hints**: Required for function signatures
- **Docstrings**: Include for public functions and classes
- **Comments**: Only for non-obvious logic

### 13.2 Adding a New Endpoint

1. Define Pydantic schema in `models/schemas.py`
2. Implement business logic in `services/`
3. Create route in appropriate `routers/` file
4. Add tests in `dts-test/`
5. Update this specification

### 13.3 Database Migrations

SQLite doesn't have built-in migration tools. For schema changes:

1. Update table definitions in `db/database.py`
2. Add migration logic (ALTER TABLE, CREATE TABLE)
3. Test migration on development database
4. Document schema version in `config.py`

### 13.4 Performance Optimization

- **Indexing**: Index frequently queried columns (symbol, time, status)
- **Connection Pooling**: Reuse MT5 connection across requests
- **Batch Operations**: Insert ticks/klines in batches (100+) to reduce I/O
- **Caching**: Cache quotes and symbols list (5-second TTL)

---

## 14. Troubleshooting

### Issue: MT5 Bridge Connection Timeout

**Symptom**: `TimeoutError: No response from MT5 at 127.0.0.1:8001`

**Solutions**:
1. Verify MT5 Docker container is running: `docker ps | grep metatrader5`
2. Check firewall: `netstat -an | grep 8001`
3. Restart bridge: `bash scripts/restart_mt5_bridge.sh`
4. Check logs: `docker logs <container-id>`

### Issue: Database is Locked

**Symptom**: `sqlite3.OperationalError: database is locked`

**Solutions**:
1. Ensure only one service instance is running
2. Kill any orphaned processes: `lsof -i :8000`
3. Delete lock file: `rm data/dts_main.db-wal`
4. Restart service

### Issue: High Trade Latency

**Symptom**: Orders taking >500ms from request to execution

**Diagnosis**:
1. Check network latency: `ping 152.32.201.243`
2. Monitor MT5 bridge load: `top` or `htop`
3. Check database write performance: Run test queries
4. Review log timestamps for bottlenecks

---

## 15. Compliance and Audit

### 15.1 Audit Trail

All trades are logged to the `orders` table with:
- `order_id`: Unique identifier
- `comment`: "DMAS-API" tag
- `opened_at` / `closed_at`: Exact timestamps
- `entry_price`, `exit_price`: Execution prices
- `realized_pnl`: Final profit/loss

### 15.2 Compliance Query

```sql
-- Get all DMAS-API trades from last 30 days
SELECT * FROM orders
WHERE comment = 'DMAS-API'
  AND opened_at > datetime('now', '-30 days')
ORDER BY opened_at DESC;
```

### 15.3 Risk Reporting

**Monthly Report**:
- Total trades executed
- Win/loss ratio
- Largest drawdown
- Average position size
- Total realized P&L

---

## Appendix A: Example Workflows

### Workflow 1: Place and Manage a Trade

```
1. POST /api/trading/orders
   - symbol: EURUSD
   - action: buy
   - volume: 0.01
   - stop_loss: 1.0900

2. Receive order_id = 12345

3. GET /api/trading/orders/12345
   - Monitor floating P&L

4. PUT /api/trading/orders/12345
   - Update take_profit to 1.1010

5. DELETE /api/trading/orders/12345
   - Close position at market
   - Receive realized_pnl
```

### Workflow 2: Multi-Timeframe Technical Analysis with Klines

```
1. GET /api/data/klines/EURUSD?timeframe=M1&count=100
   - Receive 100 latest 1-minute candles
   - Direct from MT5, real-time data

2. GET /api/data/klines/EURUSD?timeframe=H1&count=24
   - Receive 24 hourly candles (last 24 hours)
   - Aggregated from M1: each H1 = 60 M1 bars combined

3. GET /api/data/klines/EURUSD?timeframe=D1&count=5
   - Receive 5 daily candles (last 5 days)
   - Aggregated from M1: each D1 = 1440 M1 bars combined

4. Analyze OHLCV across timeframes:
   - M1: Detect entry/exit points, scalping
   - H1: Identify intraday trends
   - D1: Determine macro direction

5. Optional: Calculate technical indicators
   GET /api/data/indicators?symbol=EURUSD&timeframe=H1&indicator=RSI&period=14

6. Execute trade based on multi-timeframe confluence
   POST /api/trading/orders (with stop_loss required by SAFE-02)
```

**Aggregation Example**:
```
Input:  60 M1 candles from 1:00 PM - 1:59 PM
        [1:00] O:1.0940 H:1.0945 L:1.0935 C:1.0942
        [1:01] O:1.0942 H:1.0950 L:1.0941 C:1.0948
        ...
        [1:59] O:1.0947 H:1.0949 L:1.0946 C:1.0947

Output: 1 H1 candle
        O:1.0940 (first M1 open)
        H:1.0950 (max of all M1 highs)
        L:1.0935 (min of all M1 lows)
        C:1.0947 (last M1 close)
        V:sum(all M1 volumes)
```

---

**End of Specification**
For questions or updates, contact the development team.
