# DTS Service - 数据采集服务
# 负责从 MT5 获取实时行情并存入 SQLite

import sqlite3
from mt5linux import MT5Bridge
import os

DB_PATH = "/home/gmag11/mt5-service/config/dts_main.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ticks (
            symbol TEXT,
            time INTEGER,
            bid REAL,
            ask REAL
        )
    ''')
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("DTS Service 启动中...")
    if not os.path.exists(os.path.dirname(DB_PATH)):
        os.makedirs(os.path.dirname(DB_PATH))
    init_db()
    print(f"数据库初始化完成: {DB_PATH}")
