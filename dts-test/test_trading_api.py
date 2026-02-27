import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dts-service"))

import pytest


API_KEY_HEADER = {"X-API-Key": "test-key"}


class TestTradingAuth:
    def test_no_api_key_rejected(self, client):
        resp = client.get("/api/trading/positions")
        assert resp.status_code == 422  # missing required header

    def test_wrong_api_key_rejected(self, client):
        resp = client.get("/api/trading/positions", headers={"X-API-Key": "wrong"})
        assert resp.status_code == 403

    def test_valid_api_key(self, client):
        resp = client.get("/api/trading/positions", headers=API_KEY_HEADER)
        assert resp.status_code == 200


class TestPlaceOrder:
    def test_market_buy(self, client):
        resp = client.post("/api/trading/orders", json={
            "symbol": "EURUSD",
            "order_type": "BUY",
            "volume": 0.01,
            "stop_loss": 1.09,
        }, headers=API_KEY_HEADER)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["retcode"] == 10009

    def test_missing_stop_loss_rejected(self, client):
        resp = client.post("/api/trading/orders", json={
            "symbol": "EURUSD",
            "order_type": "BUY",
            "volume": 0.01,
        }, headers=API_KEY_HEADER)
        assert resp.status_code == 422  # Pydantic validation

    def test_over_lot_size_rejected(self, client):
        resp = client.post("/api/trading/orders", json={
            "symbol": "EURUSD",
            "order_type": "BUY",
            "volume": 0.1,
            "stop_loss": 1.09,
        }, headers=API_KEY_HEADER)
        assert resp.status_code == 422  # Pydantic le=0.01

    def test_live_server_rejected(self, client, fake_mt5):
        """SAFE-01: Trading on non-demo server is blocked at service layer."""
        from conftest import FakeAccount
        fake_mt5.account = FakeAccount(server="ICMarketsSC-Live")
        resp = client.post("/api/trading/orders", json={
            "symbol": "EURUSD",
            "order_type": "BUY",
            "volume": 0.01,
            "stop_loss": 1.09,
        }, headers=API_KEY_HEADER)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is False
        assert "SAFE-01" in body["message"]


class TestPositions:
    def test_list_positions(self, client):
        resp = client.get("/api/trading/positions", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        body = resp.json()
        assert len(body["positions"]) == 1

    def test_close_position(self, client):
        resp = client.delete("/api/trading/positions/100", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True


class TestPendingOrders:
    def test_list_pending_orders(self, client):
        resp = client.get("/api/trading/orders", headers=API_KEY_HEADER)
        assert resp.status_code == 200
        body = resp.json()
        assert body["orders"] == []
