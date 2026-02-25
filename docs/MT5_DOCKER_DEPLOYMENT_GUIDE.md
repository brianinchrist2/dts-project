商业级 MetaTrader 5 Docker 部署与数据服务集成指南

本指南介绍如何使用 gmag11/metatrader5-docker 镜像在 Linux/Windows 環境下部署 MetaTrader 5 (MT5)。該方案集成了 KasmVNC（基於瀏覽器的遠程桌面）和 mt5linux（Python 橋接服務），是構建自動化數據服務（Data Service）的最佳實踐。

1. 方案優勢
跨平台運行：在 Linux 服務器上完美運行 Windows 版 MT5。
現代遠程接入：無需安裝 VNC 客戶端，直接通過 Chrome/Edge 瀏覽器看盤。
數據調用無縫銜接：內置 mt5linux，允許外部 Python 腳本像調用官方庫一樣獲取行情。
環境隔離：容器化部署，避免 Windows 系統更新或崩潰影響交易邏輯。

2. 系統要求
操作系統：支持 Docker 的 Linux (Ubuntu 22.04+ 推薦), Windows 10/11 (WSL2), 或 macOS。
硬件配置：CPU: 至少 2 核 (Wine 指令轉換較耗資源)。
內存: 至少 4GB (MT5 運行建議預留充足內存以防 OOM 崩潰)。
磁盤: 10GB 以上可用空間。

3. 安裝步驟
第一步：安裝 Docker
確保您的系統已安裝 Docker 和 Docker Compose。
Linux: 參照 Docker 官方安裝手冊。
Windows: 安裝 Docker Desktop 並啟用 WSL2 模式。

第二步：創建工作目錄
在宿主機創建持久化目錄，用於存儲賬號信息、歷史數據和日誌。
mkdir -p ~/mt5-service/config 
cd ~/mt5-service 

第三步：編寫 docker-compose.yml
創建配置文件，定義容器運行參數。
version: '3.8' 
services: 
  mt5-server: 
    image: ghcr.io/gmag11/metatrader5-docker:latest 
    container_name: mt5_service 
    restart: always 
    ports: 
      - "3000:3000" # Web VNC 訪問端口 
      - "8001:8001" # Python mt5linux 橋接端口 
    environment: 
      # --- 遠程桌面安全設置 --- 
      - CUSTOM_USER=admin # 瀏覽器登錄名 
      - PASSWORD=your_secure_password # 瀏覽器登錄密碼 (請修改) 
      # --- MT5 自動化登錄 (可選) --- 
      - MT5_LOGIN=12345678 # MT5 賬號 
      - MT5_PASSWORD=your_trading_pass # MT5 交易密碼 
      - MT5_SERVER=Broker-Server-Name # 經紀商服務器地址 
      # --- 系統環境 --- 
      - TZ=Asia/Shanghai # 時區設置 
      - VNC_RESOLUTION=1280x720 # 窗口分辨率 
    volumes: 
      - ./config:/config # 關鍵：持久化配置和數據卷 
    deploy: 
      resources: 
        limits: 
          memory: 4G # 限制最大內存防止宿主機宕機 

第四步：啟動服務
在目錄中執行以下命令：
docker-compose up -d 
首次運行會下載約 2GB-4GB 的鏡像文件。
啟動後，可以使用 docker logs -f mt5_service 查看初始化進度。

4. 訪問與配置
4.1 訪問圖形界面
打開瀏覽器，輸入：http://服務器IP:3000
輸入你在配置中設置的 admin 和密碼。
你將看到一個運行在 Debian 上的極簡桌面，MT5 正在其中運行。

4.2 手動初始化
如果自動登錄失敗，可以在 VNC 界面內：
點擊右鍵或使用菜單打開 MT5。
執行 文件 (File) -> 登錄到交易賬戶 (Login to Trade Account)。
登錄成功後，MT5 會開始下載歷史行情。

5. 開發 Data Service (Python)
由於 MT5 運行在 Docker 的 Wine 環境中，傳統的 MetaTrader5 庫無法直接連接。我們需要使用配套的 mt5linux 庫。

5.1 安裝客戶端庫
在你的開發機（宿主機或其他容器）執行：
pip install mt5linux 

5.2 調用示例
創建一個 data_service.py 腳本來抓取數據：
from mt5linux import MetaTrader5 
import time 

# 連接到 Docker 容器 
# 如果腳本在宿主機運行，host 設為 'localhost' 
mt5 = MetaTrader5(host='localhost', port=8001) 

def start_service(): 
    if not mt5.initialize(): 
        print("連接失敗，請確保 Docker 容器內的 MT5 已啟動且 8001 端口已映射") 
        return 
    print("Data Service 已啟動...") 
    try: 
        while True: 
            # 獲取實時報價 
            tick = mt5.symbol_info_tick("EURUSD") 
            if tick: 
                print(f"EURUSD 實時價: Bid={tick.bid}, Ask={tick.ask}") 
            # 這裡可以添加邏輯：將數據權限寫入數據庫或發送到消息隊列 
            time.sleep(1) 
    except KeyboardInterrupt: 
        print("服務停止") 
    finally: 
        mt5.shutdown() 

if __name__ == "__main__": 
    start_service() 

6. 維護與最佳實踐
6.1 自動更新
gmag11 鏡像在啟動時會自動檢測並更新 MT5。
建議每週末（休市期間）重啟一次容器：docker-compose restart。
定期拉取最新鏡像以更新 Wine 版本：docker-compose pull && docker-compose up -d。

6.2 性能優化
減少圖表數量：在 VNC 界面中關閉不需要的貨幣對窗口，減少內存壓力。
設置最大柱數：在 MT5 工具 -> 選項 -> 圖表 中，將“圖表中最大柱數”設置為 5000，可顯著降低 RAM 佔用。

6.3 安全建議
防火牆隔離：不要將 3000 和 8001 端口對公網全開放。建議使用雲服務器的安全組規則，僅允許你的固定 IP 訪問。
強密碼：環境變量中的 PASSWORD 決定了 VNC 的控制權，請務必使用高強度密碼。

本指南由 AI 助手生成，旨在輔助開發者快速構建量化交易基礎設施。
