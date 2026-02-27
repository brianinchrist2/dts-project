import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dts-service"))

import pytest
from pydantic import ValidationError
from models.schemas import OrderRequest, QuoteItem, KlineItem, AccountInfo


class TestOrderRequest:
    def test_valid_market_order(self):
        req = OrderRequest(
            symbol="EURUSD",
            order_type="BUY",
            volume=0.01,
            stop_loss=1.09,
        )
        assert req.symbol == "EURUSD"
        assert req.volume == 0.01

    def test_stop_loss_required(self):
        """SAFE-02: stop_loss has no default — must be provided."""
        with pytest.raises(ValidationError, match="stop_loss"):
            OrderRequest(symbol="EURUSD", order_type="BUY", volume=0.01)

    def test_volume_over_limit_rejected(self):
        """SAFE-03: Pydantic le=0.01 constraint."""
        with pytest.raises(ValidationError, match="volume"):
            OrderRequest(
                symbol="EURUSD", order_type="BUY", volume=0.02, stop_loss=1.09
            )

    def test_volume_zero_rejected(self):
        with pytest.raises(ValidationError, match="volume"):
            OrderRequest(
                symbol="EURUSD", order_type="BUY", volume=0, stop_loss=1.09
            )

    def test_invalid_order_type_rejected(self):
        with pytest.raises(ValidationError, match="order_type"):
            OrderRequest(
                symbol="EURUSD", order_type="INVALID", volume=0.01, stop_loss=1.09
            )

    def test_pending_order_with_price(self):
        req = OrderRequest(
            symbol="EURUSD",
            order_type="BUY_LIMIT",
            volume=0.01,
            price=1.08,
            stop_loss=1.07,
            take_profit=1.10,
        )
        assert req.price == 1.08


class TestQuoteItem:
    def test_valid_quote(self):
        q = QuoteItem(symbol="EURUSD", bid=1.1, ask=1.1002, time=1700000000)
        assert q.bid == 1.1


class TestKlineItem:
    def test_valid_kline(self):
        k = KlineItem(time=1700000000, open=1.1, high=1.11, low=1.09, close=1.105, volume=100)
        assert k.high == 1.11


class TestAccountInfo:
    def test_valid_account(self):
        a = AccountInfo(
            login=12345, name="Test", server="Demo",
            balance=10000, equity=10000, margin=0,
            margin_free=10000, leverage=100, currency="USD",
        )
        assert a.login == 12345
