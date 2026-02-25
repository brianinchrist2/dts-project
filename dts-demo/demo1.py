from mt5linux import MetaTrader5
from datetime import datetime
import time

def main():
    # 连接配置
    host = "127.0.0.1"
    port = 8001
    
    print(f"--- 正在连接 MT5 Bridge ({host}:{port}) ---")
    mt5 = MetaTrader5(host, port)
    
    # 初始化
    if not mt5.initialize():
        print(f"initialize() 失败, error code = {mt5.last_error()}")
        # return # 有些版本不需要显式 initialize 也能获取基本信息，继续尝试
    
    # 1. 获取账户信息
    print("\n[1/2] 获取账户信息...")
    account_info = mt5.account_info()
    if account_info is not None:
        print(f"账户 ID: {account_info.login}")
        print(f"持有者: {account_info.name}")
        print(f"余额: {account_info.balance} {account_info.currency}")
        print(f"净值: {account_info.equity}")
        print(f"杠杆: 1:{account_info.leverage}")
    else:
        print("错误: 无法获取账户信息。请确保 MT5 已登录。")

    # 2. 获取交易历史记录 (过去 30 天)
    print("\n[2/2] 获取交易历史记录 (最近 30 天)...")
    from_date = time.time() - (30 * 24 * 60 * 60) # 30天前
    to_date = time.time()
    
    # 获取历史成交记录 (Deals)
    history_deals = mt5.history_deals_get(from_date, to_date)
    
    if history_deals is None:
        print("错误: 无法获取历史记录。")
    elif len(history_deals) == 0:
        print("未发现最近 30 天的交易历史。")
    else:
        print(f"成功获取到 {len(history_deals)} 条成交记录:")
        for deal in history_deals[:10]:  # 仅显示前 10 条
            deal_time = datetime.fromtimestamp(deal.time).strftime('%Y-%m-%d %H:%M:%S')
            print(f"- 时间: {deal_time}, 品种: {deal.symbol}, 类型: {deal.type}, 利润: {deal.profit}")
        if len(history_deals) > 10:
            print(f"... 以及另外 {len(history_deals) - 10} 条记录。")

if __name__ == "__main__":
    main()
