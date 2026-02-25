from mt5linux import MT5Bridge
import time

def run_demo():
    # 连接配置
    host = "152.32.201.243"
    port = 8001
    
    print(f"正在尝试连接到 MT5 Bridge: {host}:{port}...")
    
    try:
        # 初始化连接
        mt5 = MT5Bridge(host, port)
        
        # 获取版本信息
        ver = mt5.version()
        print(f"成功连接！MT5 版本: {ver}")
        
        # 获取账户信息
        account = mt5.account_info()
        if account:
            print(f"账户信息: {account}")
        else:
            print("未能获取账户信息，请确认 MT5 已登录。")
            
        # 获取前 5 个品种
        symbols = mt5.symbols_get()
        if symbols:
            print(f"前 5 个交易品种: {[s.name for s in symbols[:5]]}")
            
    except Exception as e:
        print(f"连接失败: {e}")

if __name__ == "__main__":
    run_demo()
