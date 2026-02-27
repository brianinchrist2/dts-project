import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dts-service"))

import pytest
from services.safety import (
    SafetyError,
    check_demo_account,
    check_stop_loss,
    check_lot_size,
    enforce_comment,
    run_all_pre_trade_checks,
)


class TestSAFE01DemoAccount:
    def test_allowed_server_passes(self):
        check_demo_account("ICMarketsSC-Demo")

    def test_live_server_rejected(self):
        with pytest.raises(SafetyError, match="SAFE-01"):
            check_demo_account("ICMarketsSC-Live")

    def test_empty_server_rejected(self):
        with pytest.raises(SafetyError, match="SAFE-01"):
            check_demo_account("")


class TestSAFE02StopLoss:
    def test_positive_sl_passes(self):
        check_stop_loss(1.0900)

    def test_zero_sl_rejected(self):
        with pytest.raises(SafetyError, match="SAFE-02"):
            check_stop_loss(0)

    def test_negative_sl_rejected(self):
        with pytest.raises(SafetyError, match="SAFE-02"):
            check_stop_loss(-1.0)


class TestSAFE03LotSize:
    def test_min_lot_passes(self):
        check_lot_size(0.01)

    def test_over_limit_rejected(self):
        with pytest.raises(SafetyError, match="SAFE-03"):
            check_lot_size(0.02)

    def test_zero_volume_rejected(self):
        with pytest.raises(SafetyError, match="SAFE-03"):
            check_lot_size(0)

    def test_negative_volume_rejected(self):
        with pytest.raises(SafetyError, match="SAFE-03"):
            check_lot_size(-0.01)


class TestSAFE04Comment:
    def test_enforced_comment(self):
        assert enforce_comment() == "DMAS-API"


class TestRunAllPreTradeChecks:
    def test_all_pass(self):
        comment = run_all_pre_trade_checks(
            server="ICMarketsSC-Demo", volume=0.01, stop_loss=1.09
        )
        assert comment == "DMAS-API"

    def test_live_server_fails(self):
        with pytest.raises(SafetyError, match="SAFE-01"):
            run_all_pre_trade_checks(
                server="ICMarketsSC-Live", volume=0.01, stop_loss=1.09
            )

    def test_over_lot_fails(self):
        with pytest.raises(SafetyError, match="SAFE-03"):
            run_all_pre_trade_checks(
                server="ICMarketsSC-Demo", volume=0.1, stop_loss=1.09
            )

    def test_no_sl_fails(self):
        with pytest.raises(SafetyError, match="SAFE-02"):
            run_all_pre_trade_checks(
                server="ICMarketsSC-Demo", volume=0.01, stop_loss=0
            )
