import unittest
from mt5linux import MetaTrader5

class TestMT5Connection(unittest.TestCase):
    def setUp(self):
        self.host = "152.32.201.243"
        self.port = 8001
        self.bridge = MetaTrader5(self.host, self.port)

    def test_ping(self):
        """测试基础连接是否通畅"""
        try:
            ok = self.bridge.initialize()
            self.assertTrue(ok)
            version = self.bridge.version()
            self.assertIsNotNone(version)
        except Exception as e:
            self.fail(f"MT5 connection failed: {e}")
        finally:
            self.bridge.shutdown()
