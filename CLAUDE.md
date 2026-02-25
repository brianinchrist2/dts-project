# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DTS** (MetaTrader 5 Docker Automation) is an automated trading system that communicates with MetaTrader 5 via the `mt5linux` library over TCP port 8001. The system connects to a containerized MT5 instance (`ghcr.io/gmag11/metatrader5-docker`) and provides APIs for algorithmic trading.

### Directory Structure

- **`dts-service/`**: Core automation logic (data collection, order execution, risk management)
- **`dts-demo/`**: Example scripts demonstrating MT5 API usage (account info, symbols, trade history)
- **`dts-test/`**: Unit tests using Python's `unittest` framework (connection tests, order logic validation)
- **`scripts/`**: Operational scripts for MT5 Bridge maintenance and container management
- **`docs/`**: API documentation, trading strategy specs, backtest reports (reserved)

### Key Dependencies

- **mt5linux**: Python bridge for MT5 communication (imported in all modules)
- **sqlite3**: Data persistence for tick data and trading history
- Python 3.9+ (as specified in deployment)

---

## Development Commands

### Running Tests

```bash
# Run all tests
python -m unittest discover -s dts-test -p "test_*.py"

# Run specific test file
python dts-test/test_connection.py

# Run with verbose output
python -m unittest discover -s dts-test -p "test_*.py" -v
```

### Running Demos

```bash
# Demo 1: Account info and trade history
python dts-demo/demo1.py

# MT5 connection test (basic connectivity)
python dts-demo/mt5_conn_demo.py
```

### Running the Main Service

```bash
# Start data collection service
python dts-service/main.py
```

### MT5 Bridge Maintenance

```bash
# Restart the MT5 Bridge (if unresponsive)
bash scripts/restart_mt5_bridge.sh
```

---

## Architecture & Connection Model

### MT5 Bridge Communication

- **Remote Host**: `152.32.201.243:8001` (production/development)
- **Local Host**: `127.0.0.1:8001` (local development with Docker)
- **Protocol**: TCP/IP via `MT5Bridge` or `MetaTrader5` class from `mt5linux`
- **Data Storage**: SQLite database at `/home/gmag11/mt5-service/config/dts_main.db`

### Code Patterns

**Initialization Pattern** (see `dts-demo/demo1.py`):
```python
from mt5linux import MetaTrader5
mt5 = MetaTrader5(host, port)
if not mt5.initialize():
    print(f"Error: {mt5.last_error()}")
```

**Database Schema** (see `dts-service/main.py`):
- `ticks` table: `(symbol TEXT, time INTEGER, bid REAL, ask REAL)`
- Auto-created on service startup

**Testing Pattern** (see `dts-test/test_connection.py`):
- Use `unittest.TestCase` with `setUp()` for bridge initialization
- Test core APIs: `version()`, `account_info()`, `symbols_get()`

---

## Trading Safety Rules (Non-Negotiable)

These rules are enforced per **DTS_DEVELOPMENT_GUIDE.md** and must be followed strictly:

1. **[SAFE-01] Demo Accounts Only**: All trading must target `ICMarketsSC-Demo` server unless explicitly authorized by Brian
2. **[SAFE-02] Stop Loss Enforcement**: Every open position must include a `stop_loss` parameter (no exceptions)
3. **[SAFE-03] Lot Size Limits**: Test trades limited to **0.01 lots** (minimum position size)
4. **[SAFE-04] API Logging**: All executed trades must include `comment: "DMAS-API"` for audit trail

---

## Development Workflow (EDD)

### Before Starting a Task

1. **Define Success Criteria** in task description (e.g., "Connection latency < 500ms", "Order execution success rate > 99%")
2. **Check for Existing Tests** in `/dts-test/` to understand the expected behavior
3. **Review Trading Rules** if modifying order execution logic

### Making Changes

- **Prefer `edit` over `write`**: Use the Edit tool for single-file changes to preserve context
- **Add Tests First** when adding new trading logic (e.g., new order types, risk checks)
- **Update Database Schema** in `dts-service/main.py` if adding new data fields
- **Include Comments** only for non-obvious logic (avoid redundant comments on simple code)

### Verification

- Run the relevant test suite before committing
- For order logic: verify against demo account first (never live accounts)
- Check bridge connectivity with `dts-demo/mt5_conn_demo.py` if network issues suspected

---

## Common Pitfalls

1. **IP/Port Hardcoding**: Demos use different IPs (127.0.0.1 vs 152.32.201.243). Tests must work against configured endpoint.
2. **Missing `initialize()`**: Some MT5Bridge versions require explicit `initialize()` before API calls; others don't. Handle both cases gracefully.
3. **Database Locking**: SQLite allows only one write at a time. If tests fail with "database is locked", ensure teardown closes connections.
4. **Demo vs Live**: Always verify new trading code targets `ICMarketsSC-Demo` before deployment.

---

## Reference Files

- **DTS_DEVELOPMENT_GUIDE.md**: Full project guidelines, safety rules, and collaboration protocols
- **Main Service**: `dts-service/main.py` (data schema and initialization)
- **Test Template**: `dts-test/test_connection.py` (unittest structure)
- **Demo Examples**: `dts-demo/demo1.py`, `dts-demo/mt5_conn_demo.py`
