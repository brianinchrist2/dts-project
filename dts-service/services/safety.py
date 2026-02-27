"""
Safety rule enforcement (defense-in-depth).

SAFE-01: Demo accounts only — reject if account server != allowed_server
SAFE-02: Stop loss required — enforced at Pydantic layer (OrderRequest.stop_loss)
SAFE-03: Lot size limit  — enforced at Pydantic layer (Field(le=0.01)) + config check
SAFE-04: Comment override — trading_service injects trade_comment on every order
"""

import logging

from config import settings

logger = logging.getLogger(__name__)


class SafetyError(Exception):
    """Raised when a trading safety rule is violated."""

    def __init__(self, rule: str, message: str) -> None:
        self.rule = rule
        self.message = message
        super().__init__(f"[{rule}] {message}")


def check_demo_account(server: str) -> None:
    """SAFE-01: Ensure we are trading on the allowed demo server."""
    if server != settings.allowed_server:
        raise SafetyError(
            "SAFE-01",
            f"Trading blocked: server '{server}' is not the allowed demo "
            f"server '{settings.allowed_server}'",
        )
    logger.debug("SAFE-01 passed: server=%s", server)


def check_stop_loss(stop_loss: float) -> None:
    """SAFE-02: Ensure stop_loss is set and positive."""
    if stop_loss <= 0:
        raise SafetyError("SAFE-02", "stop_loss must be a positive value")
    logger.debug("SAFE-02 passed: sl=%s", stop_loss)


def check_lot_size(volume: float) -> None:
    """SAFE-03: Ensure volume does not exceed the configured limit."""
    if volume > settings.max_lot_size:
        raise SafetyError(
            "SAFE-03",
            f"Volume {volume} exceeds max allowed {settings.max_lot_size}",
        )
    if volume <= 0:
        raise SafetyError("SAFE-03", "Volume must be positive")
    logger.debug("SAFE-03 passed: vol=%s", volume)


def enforce_comment() -> str:
    """SAFE-04: Return the mandatory trade comment (overrides user input)."""
    return settings.trade_comment


def run_all_pre_trade_checks(server: str, volume: float, stop_loss: float) -> str:
    """Run SAFE-01 through SAFE-04 and return the enforced comment."""
    check_demo_account(server)
    check_stop_loss(stop_loss)
    check_lot_size(volume)
    return enforce_comment()
