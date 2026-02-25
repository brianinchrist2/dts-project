# DTS 項目開發規範與指南 (DTS Development Guide)

**項目名稱**: dts (MetaTrader 5 Docker Automation)
**版本**: v1.0.0
**負責人**: BigQ ⚡ (CTO)
**繼承協議**: [BIGQ_DEVELOPMENT_PROTOCOL.md](../../knowledge_base/BIGQ_DEVELOPMENT_PROTOCOL.md)

---

## 1. 項目架構與環境

### 1.1 運行環境
- **部署方式**: Docker 容器化部署 (`ghcr.io/gmag11/metatrader5-docker`)。
- **橋接機制**: 使用 `mt5linux` 庫通過 TCP Port **8001** 進行 Python 與 MT5 的通訊。
- **數據存儲**: 持久化掛載於 `/home/gmag11/mt5-service/config`。

### 1.2 目錄結構
- `/dts-service/`: 核心自動化交易邏輯與 API 服務。
- `/dts-demo/`: 各類功能展示與快速原型腳本。
- `/dts-test/`: 專屬測試套件（連接測試、下單邏輯測試）。
- `/scripts/`: 環境維護、容器重啟及日誌清理腳本。
- `/docs/`: API 文檔、交易策略 Spec 及回測報告。

---

## 2. 開發流程實施

### 2.1 任務派發與執行
所有開發任務必須遵循 **EDD (評估驅動開發)** 流程：
1. **定義指標**: 任務開始前，必須在 `TODO.md` 中明確驗收標準（例：連接成功、下單延遲 < 500ms）。
2. **原子修改**: 優先使用 `edit` 工具修改單個文件，嚴禁在大於 100 行的文件上執行全量 `write`。
3. **單元測試**: 任何邏輯變更必須伴隨 `/dts-test/` 下的新增測試用例。

### 2.2 質量門禁 (Quality Gate)
- **並行審核**: **Constructor 🔨** 提交代碼後，自動觸發 **Expert 🐲 (MiniMax)** 進行邏輯審計。
- **連接性檢查**: 所有測試必須在 MT5 容器在線且橋接通暢的情況下執行。

---

## 3. 交易安全紅線 (Trading Safeguards)

為確保資金安全，所有開發必須遵守以下硬性約束：
- **[SAFE-01] 模擬優先**: 在未經 Brian 明確授權前，所有下單操作必須指向 `ICMarketsSC-Demo` 服務器。
- **[SAFE-02] 止損強制**: 任何開倉函數必須強制要求傳入 `stop_loss` 參數，不得空倉運行。
- **[SAFE-03] 風控限額**: 單筆測試交易手數不得超過 **0.01**（最小手數）。
- **[SAFE-04] 日誌標註**: 所有通過 API 執行的操作，必須在 `comment` 欄位標註 `DMAS-API` 以便溯源。

---

## 4. 跨 Agent 協作規約

- **GLOBAL_LOG 使用**: 完成一次下單邏輯優化後，必須記錄：
  `[Constructor] Optimized order execution logic in dts-service/main.py. Eval: PASS.`
- **記憶同步**: 每天開工前，所有 Agent 必須讀取 `memory/index.md` 中關於 dts 項目的最新摘要。

---
*本指南由 BigQ ⚡ 制定，是 dts 項目開發的最高行為準則。*
