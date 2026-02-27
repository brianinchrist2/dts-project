import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "dts-service"))

import pytest


class TestSystemEndpoints:
    def test_health(self, client):
        resp = client.get("/api/system/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["mt5_connected"] is True
        assert body["db_ok"] is True

    def test_version(self, client):
        resp = client.get("/api/system/version")
        assert resp.status_code == 200
        body = resp.json()
        assert "service_version" in body


class TestDataEndpoints:
    def test_quotes(self, client):
        resp = client.get("/api/data/quotes")
        assert resp.status_code == 200
        body = resp.json()
        assert "quotes" in body
        assert len(body["quotes"]) > 0

    def test_ticks_empty(self, client):
        resp = client.get("/api/data/ticks/EURUSD?count=5")
        assert resp.status_code == 200
        body = resp.json()
        assert body["symbol"] == "EURUSD"
        assert body["ticks"] == []  # DB is empty in test

    def test_symbol_info(self, client):
        resp = client.get("/api/data/symbols/EURUSD")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "EURUSD"
        assert body["digits"] == 5


class TestAccountEndpoints:
    def test_account_info(self, client):
        resp = client.get("/api/account/info")
        assert resp.status_code == 200
        body = resp.json()
        assert body["login"] == 12345
        assert body["server"] == "ICMarketsSC-Demo"

    def test_account_history(self, client):
        resp = client.get("/api/account/history?days=7")
        assert resp.status_code == 200
        body = resp.json()
        assert "deals" in body
