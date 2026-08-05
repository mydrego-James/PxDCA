# LogicMCP Server

LogicMCP Server 是以 FastMCP 3 建置的 MCP 服務，將軟體需求探索、需求驗證、
技術對齊、規格產生與 ISO-aligned audit 整理為可重複呼叫的 MCP 能力。

服務提供：

- Prompts：定義需求探索、訪談、整合、技術對齊與 audit 的輸入輸出契約。
- Resources：提供 workflow policies、capability profiles、JSON Schemas 與 templates。
- Tools：驗證各階段 JSON payload，並產生需求、規劃、交付、軟體規格與 audit 文件。

LogicMCP Server 不包含 LLM 或使用者介面。模型選擇、對話狀態及 workflow 呼叫
順序由 VS Code 或其他 MCP Client 管理。

## 系統需求

- Git
- Windows
- Python 3.11 或更新版本
- 支援 MCP Streamable HTTP 的 Client

## 本地建置與啟動

### 1. 取得專案

```powershell
git clone https://github.com/mydrego-James/LogicMCP_Server.git
cd LogicMCP_Server
```

### 2. 建立本地設定

```powershell
Copy-Item .env.example .env
```

本地啟動使用的 `.env` 設定：

```dotenv
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp
MCP_TRANSPORT=http
MCP_OUTPUT_ROOT=./output
```

`run.bat` 啟動時會讀取 `.env`。若設定缺漏，會使用以上預設值。

### 3. 安裝

```powershell
.\install.bat
```

安裝程式會建立 `.venv` 並安裝所需 Python dependencies。

### 4. 啟動

```powershell
.\run.bat
```

預設 endpoint：

```text
http://127.0.0.1:8000/mcp
```

Client 使用期間需保持 Server terminal 開啟。按 `Ctrl+C` 可停止服務。

## 提供給 VS Code 使用

先啟動 LogicMCP Server，然後在要使用服務的 VS Code workspace 建立：

```text
.vscode/mcp.json
```

內容如下：

```json
{
  "servers": {
    "logicmcp": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

在 VS Code 中：

1. 開啟 Command Palette（`Ctrl+Shift+P`）。
2. 執行 `MCP: List Servers`。
3. 選擇 `logicmcp` 並啟動。
4. 第一次啟動時確認信任此 MCP Server。
5. 在 Chat 的工具清單中啟用 LogicMCP 提供的 Tools、Prompts 或 Resources。

也可以執行 `MCP: Add Server`，選擇 HTTP，輸入相同 endpoint，並將設定保存到
Workspace。詳細操作見 [VS Code MCP Server 官方文件](https://code.visualstudio.com/docs/agent-customization/mcp-servers)。

## 輸出與紀錄

- 相對輸出路徑會寫入 `MCP_OUTPUT_ROOT`，預設為 `./output/`。
- Server、HTTP access 與 Tool validation logs 寫入 `./logs/fastmcp/`。
- Client 傳入絕對輸出路徑時，Server 會使用該目的地。

## 第一層目錄與檔案

```text
server/             LogicMCP Server 原始碼與 MCP 資源
logs/               Server runtime logs
output/             MCP Tools 預設輸出
tools/              Server 檢視、調教、備份與更新工具

install.bat         建立本地 Python 環境並安裝 dependencies
run.bat             讀取 .env 並啟動本地服務
requirements.txt    Python dependencies
.env.example        本地設定範本
fastmcp.json        FastMCP deployment 設定
Dockerfile          Docker image 設定
compose.yaml        Docker Compose 設定

README.md           專案目標、本地建置與使用方式
docker.md           Docker 使用說明
MAP.MD              AI 使用的專案檔案地圖
```

Docker 建置與 Compose 使用方式請見 [docker.md](docker.md)。

## 常見問題

### Port 已被占用

修改 `.env` 中的 `MCP_PORT`，再重新執行 `run.bat`。VS Code 的 MCP URL 也必須
改成相同 port。

### VS Code 找不到 Server

確認 `run.bat` 仍在執行、`.vscode/mcp.json` 的 URL 與 `.env` 一致，然後透過
`MCP: List Servers` 查看狀態或重新啟動 Server。

### Python dependencies 缺失

重新執行 `install.bat`，完成後再執行 `run.bat`。
