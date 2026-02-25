import unittest
from mt5linux import MT5Bridge

class TestMT5Connection(unittest.TestCase):
    def setUp(self):
        self.host = "152.32.201.243"
        self.port = 8001
        self.bridge = MT5Bridge(self.host, self.port)

    def test_ping(self):
        """测试基础连接是否通畅"""
        try:
            version = self.bridge.version()
            self.assertIsNotNone(version)
        except Exception as e:
            self.fail(f"MT5 Bridge connection failed: {e}")

if __name__ == '__main__':
    unittest.main()
