# LogicMCP Server Maintenance Map

用途：LogicMCP Server 的精簡維護索引。進行大範圍搜尋或修改前，先閱讀本檔案。

最後架構更新：2026-08-04。

## 1. 產品邊界

本專案的唯一產品是 LogicMCP Server；FastMCP 是其 MCP framework dependency。

正常安裝與啟動只提供：

```text
http://127.0.0.1:8000/mcp
```

Server 不選擇或呼叫 LLM，也不啟動 CLI、APP 或 Factory。根目錄的 `install.bat`、`run.bat`、`requirements.txt`、`fastmcp.json`、`Dockerfile` 與 `compose.yaml` 全部只服務 MCP Server。

## 2. 主要結構

```text
server/
  entrypoint.py                  FastMCP CLI filesystem entrypoint
  fastmcp_service/
    server.py                    Python module process entrypoint
    mcp_instance.py              FastMCP instance、output root 與 logging
    prompts.py + prompts/        MCP Prompt contracts 與 capability profiles
    resources.py + resources/    Schemas、policies、profiles 與 templates
    tools/                       MCP validators、persistence 與 renderers
    docs/                        workflow、I/O boundary、audit 與 contract baseline

tools/                           Server 檢視、調教、備份、更新等維護工具
logs/                            MCP startup、HTTP/API 與 Tool logs
output/                          MCP 自有檔案產出的預設位置
```

不得恢復舊的 `mcp_servers/logic_mcp_server/` 階層，也不得把 Client／Factory 程式放回本 repository。

## 3. 公開 MCP 契約

目前基線：

- Tools：16
- Prompts：9
- Resources：12

詳細名稱、URI 與必要輸入欄位記錄於 `server/fastmcp_service/docs/contract-baseline.json`。修改 FastMCP framework、Prompt、Schema 或 Tool 時，必須先驗證此公開契約；不得因內部重構任意改名或移除。

## 4. 依賴規則

- `server/fastmcp_service/` 不得 import LogicMCP Client、Factory、LLM 或 APP。
- 根目錄 `tools/` 只放 Server 維護工具，不放使用者端 CLI。
- Server 可透過 MCP Prompt 提供 LLM contract，但 Server 自己不呼叫 LLM。
- 所有 MCP 註冊由 `server.py` 匯入 Prompts、Resources 與 Tools 完成。
- FastMCP deployment 設定放在 `mcp.run(...)` 或 `fastmcp.json`，不放回舊式 constructor 設定。

## 5. Logs 與 output

- `logs/fastmcp/`：Server 啟動、停止、HTTP request/response status、validation evidence 與 MCP Tool 執行紀錄。
- `output/`：Client 傳入相對輸出路徑時的 MCP 預設產出根目錄。
- Client 傳入絕對路徑時，Renderer 可以輸出到 Client 擁有的位置；Server 不因此依賴 Client internals。
- HTTP access log 不複製 request／response body。

完整規則請閱讀 `server/fastmcp_service/docs/IO_BOUNDARY.md`。

## 6. 維護焦點

1. 維持 `install.bat -> run.bat -> 127.0.0.1:8000/mcp` 的獨立部署能力。
2. 維持 FastMCP 3 與 `fastmcp.json` 的官方使用方式。
3. 保護 Prompts、Tools、Resources、Schemas 與 Templates 的 LogicMCP 邏輯。
4. Server 改版後比對 contract baseline 並執行實際 MCP initialize/list/call 測試。
5. 開源前排除 `.env`、`.venv`、`__pycache__`、實際 logs、output 與任何 credential。
