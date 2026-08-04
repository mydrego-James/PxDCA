# LogicMCP Server 改版前檢視紀錄

檢視日期：2026-08-04

## 本輪範圍

主體只有 `server/fastmcp_service` 與支援它安裝、啟動的根目錄檔案。
`factory/`、根目錄維護用 `tools/` 與未建立的 APP 都不是 Server 的相依項目。

後續邊界修正：使用者端 CLI 已歸入獨立的 `factory/cli/`；根目錄
`tools/` 僅保留 MCP 檢視、調教、備份及更新工具。根目錄 `logs/` 僅供
MCP Server 使用，MCP 自有檔案產出的預設位置則獨立為根目錄 `output/`。

## 產品與框架邊界

- 產品是 LogicMCP Server。
- FastMCP 是 LogicMCP 使用的 MCP 框架，不是本專案要重新開發的產品。
- 正式服務位址是 `http://127.0.0.1:8000/mcp`。
- Server 必須能獨立安裝、獨立啟動，不依賴 CLI、LLM、APP 或工廠控制層。

## 改版前狀態

- 執行框架：MCP Python SDK 內嵌的舊版 `mcp.server.fastmcp.FastMCP`。
- 套件限制：`mcp>=1.2.0,<2.0`。
- 部署參數放在 `FastMCP(...)` 建構式，屬於舊 API 寫法。
- Server logger 曾依賴已移除的 `logs.log_client`；目前已改成 Server 自包含的標準 Python logging。
- 舊服務可在 `127.0.0.1:8000/mcp` 啟動並完成 MCP initialize/list 操作。

## 公開 MCP 契約基線

- Tools：16
- Prompts：9
- Resources：12
- 詳細名稱、URI、參數與必要欄位存於 `contract-baseline.json`。

升級驗收規則：上述公開名稱與輸入契約不得因 FastMCP 框架升級而消失或改名。

## 結構完整性

- 20 個 profile 宣告均有對應 prompt profile 檔案，沒有缺檔或孤兒 profile。
- Prompts、Tools、Resources 均由 `server.py` 匯入註冊。
- Schema、policy 與 renderer template 均位於 Server 套件內，不依賴外部功能層。

## 查到但暫不刪除的殘留候選

下列檔案目前沒有被 Server runtime 直接引用：

- `docs/examples/minimal_workflow_client.py`：舊示意客戶端，內容不是可執行的正式 Client。
- `resources/templates/audit/iso-aligned-audit.json`
- `resources/templates/translation/english-shadow-audit.json`
- `resources/templates/policies/README.md`

它們不影響啟動，也不是已註冊的 MCP 公開能力。為避免在框架改版時誤刪可能保留的領域素材，本輪只記錄、不刪除。

## 已註冊但附加工廠目前未使用的能力

部分公開 Tool/Prompt 尚未被目前的附加工廠流程呼叫。這不代表它們是 Server 殘留；對 MCP Client 而言，它們仍是公開契約，因此本輪全部保留。

## 改版決策

- 改用獨立套件 `fastmcp==3.4.5`（當時的 FastMCP 3 穩定版本）。
- 改用 `from fastmcp import FastMCP`。
- host、port、path 等部署設定移到 `mcp.run(...)`。
- 新增 `fastmcp.json`，讓熟悉 FastMCP 的 Python 使用者可用官方 CLI 辨識專案。
- 保持 `run.bat` 為正式的 localhost HTTP MCP 啟動入口。

## 改版後驗證

- `fastmcp inspect fastmcp.json --format mcp`：通過。
- `fastmcp run fastmcp.json`：成功啟動同一個 localhost MCP endpoint。
- `run.bat`：成功啟動 `http://127.0.0.1:8000/mcp`。
- HTTP MCP initialize 與 list：通過。
- 契約比對：16 Tools、9 Prompts、12 Resources 的名稱與必要輸入欄位全部相符。
- 實際呼叫：`get_available_templates`、`consultant_plan_review`、`config://logicmcp` 均成功回傳。
- Python compile：通過。
