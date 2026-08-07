# LogicMCP Server

LogicMCP Server 是以 FastMCP 3 建置的需求工程服務。對 MCP Client 僅公開三個方法，分別完成需求書、架構書與稽核報告；問題生成、LLM Sampling、Schema 驗證、狀態轉移及文件渲染都封裝在 Server 內部。

公開方法：

- `generate_requirements`：從 Q0 建立 Q1～Qn 訪談，持久化每次回答並產生需求書。
- `generate_architecture`：讀取已完成的需求工作階段，產生對齊需求的架構書。
- `run_audit`：稽核同一工作階段的需求書與架構書，產生覆蓋與追溯報告。

Server 不公開內部 Prompts、Resources、Validators 或 Renderers。Client 必須明確選擇上述三個入口，且必須支援 MCP Sampling，讓 Server 在封閉流程中使用 Client 的 LLM。

## 本地建置

需求：Git、Windows、Python 3.11 以上。

### 1. 取得專案

```powershell
git clone https://github.com/mydrego-James/LogicMCP_Server.git
cd LogicMCP_Server
```

### 2. 建立環境設定

```powershell
Copy-Item .env.example .env
```

主要設定：

```dotenv
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp
MCP_TRANSPORT=http
MCP_OUTPUT_ROOT=./output
MCP_STATE_ROOT=./output/.logicmcp/sessions
```

`MCP_STATE_ROOT` 保存需求訪談狀態。若要在隔天或 Server 重啟後接續，該目錄不得使用暫存磁碟。

### 3. 安裝

```powershell
.\install.bat
```

### 4. 啟動

```powershell
.\run.bat
```

預設 MCP endpoint：

```text
http://127.0.0.1:8000/mcp
```

## VS Code 設定

在使用 LogicMCP 的 VS Code workspace 建立 `.vscode/mcp.json`：

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

開啟 Command Palette，執行 `MCP: List Servers`，確認 `logicmcp` 已啟動。Client 只會看到三個 LogicMCP Tools。

## 使用方式

### 建立需求書

第一次呼叫：

```json
{
  "tool": "generate_requirements",
  "arguments": {
    "q0": "建立一套設備維護管理系統",
    "profile": "professional"
  }
}
```

Server 回傳 `session_id`、完整 Q1～Qn 題庫及目前問題。回答時仍呼叫同一個 Tool：

```json
{
  "tool": "generate_requirements",
  "arguments": {
    "session_id": "SERVER_RETURNED_SESSION_ID",
    "answer": "由維修主管與現場技師使用。"
  }
}
```

若關閉 Client 或隔天繼續，只傳入 `session_id` 即可取得上次進度與待回答問題：

```json
{
  "tool": "generate_requirements",
  "arguments": {
    "session_id": "SERVER_RETURNED_SESSION_ID"
  }
}
```

工作階段狀態不依賴 MCP 連線。每次通過驗證的回答都會先寫入 `MCP_STATE_ROOT`，再進入下一階段。

### 建立架構書

需求書完成後呼叫：

```json
{
  "tool": "generate_architecture",
  "arguments": {"session_id": "SERVER_RETURNED_SESSION_ID"}
}
```

### 執行稽核

架構書完成後呼叫：

```json
{
  "tool": "run_audit",
  "arguments": {"session_id": "SERVER_RETURNED_SESSION_ID"}
}
```

完成的呼叫具冪等性；再次使用相同 `session_id` 時，Server 會回傳既有產物，不會重複生成。

## 輸出與紀錄

- 文件預設位於 `output/<session_id>/`。
- 工作狀態預設位於 `output/.logicmcp/sessions/`。
- Server logs 位於 `logs/fastmcp/`。

## 第一層目錄

```text
server/             LogicMCP Server 程式、私有流程與資源
logs/               Server runtime logs
output/             工作階段狀態與生成文件
tools/              維護 Server 的專案工具與規劃

install.bat         安裝 Python dependencies
run.bat             載入 .env 並啟動 Server
requirements.txt    Python dependencies
.env.example        本地設定範本
fastmcp.json        FastMCP deployment 設定
Dockerfile          Docker image 設定
compose.yaml        Docker Compose 設定

README.md           專案介紹、安裝與使用方式
docker.md           Docker 使用方式
MAP.MD              AI 專用專案結構索引
```

Docker 建置與資料持久化請參考 [docker.md](docker.md)。
