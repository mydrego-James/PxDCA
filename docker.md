# LogicMCP Server — Docker 使用說明

## Image 內容與設定來源

Docker image 只包含執行服務所需的內容：

```text
requirements.txt
server/
```

`server/` 會完整複製，因此三個公開 MCP Tools 與其私有 Prompts、Resources、
Schemas、Validators、Renderers、Templates 都包含在 image 中。

部署設定不寫入 image：

```text
.env
> compose.yaml variable interpolation
> container environment / published port / bind mounts
```

`.env` 被 `.dockerignore` 排除，不會包含在 image layer。`fastmcp.json` 是
FastMCP filesystem deployment 的入口設定；Docker 使用
`python -m server.fastmcp_service`，因此不需要將它複製進 image。

## 系統需求

- Docker Engine
- Docker Compose（使用 Compose 啟動時需要）

## Docker Compose

### 1. 建立設定檔

```powershell
Copy-Item .env.example .env
```

Compose 使用以下 `.env` 設定：

```dotenv
MCP_PATH=/mcp
LOGICMCP_BIND_HOST=127.0.0.1
LOGICMCP_HOST_PORT=8000
LOGICMCP_LOG_DIR=./logs
LOGICMCP_OUTPUT_DIR=./output
```

| Variable | Compose 使用位置 | 用途 |
|---|---|---|
| `MCP_PATH` | `environment.MCP_PATH` | Container 內的 MCP endpoint path |
| `LOGICMCP_BIND_HOST` | `ports.host_ip` | 發布服務的 host IP |
| `LOGICMCP_HOST_PORT` | `ports.published` | 發布服務的 host port |
| `LOGICMCP_LOG_DIR` | `volumes.source` | 保存 logs 的 host 目錄 |
| `LOGICMCP_OUTPUT_DIR` | `volumes.source` | 保存輸出檔案的 host 目錄 |

需求訪談狀態位於 output volume 內的 `.logicmcp/sessions/`。只要
`LOGICMCP_OUTPUT_DIR` 指向持久化 host 目錄，Container 重建後仍可使用原本的
`session_id` 接續。

Container 內部設定維持固定：

| 設定 | 值 | 原因 |
|---|---|---|
| Bind host | `0.0.0.0` | 允許 Docker published port 連入 container |
| Container port | `8000` | 與 Dockerfile `EXPOSE`、port target、healthcheck 一致 |
| Transport | `http` | Compose service 透過 HTTP 對外提供 MCP |
| Output root | `/srv/logicmcp/output` | 與 output bind mount target 一致 |
| State root | `/srv/logicmcp/output/.logicmcp/sessions` | 與 output bind mount 一起持久化 |
| Log root | `/srv/logicmcp/logs` | 與 log bind mount target 一致 |

修改 `.env` 後，可先查看 Compose 實際解析結果：

```powershell
docker compose config
docker compose config --environment
```

### 2. 建置並啟動

```powershell
docker compose up --build mcp
```

預設 endpoint：

```text
http://127.0.0.1:8000/mcp
```

背景執行：

```powershell
docker compose up --build -d mcp
```

### 3. 查看狀態與 logs

```powershell
docker compose ps
docker compose logs -f mcp
```

### 4. 停止

```powershell
docker compose down
```

## Docker image

### 建置

```powershell
docker build -t logicmcp-server .
```

### 啟動

```powershell
docker run --rm `
  --name logicmcp-server `
  -p 127.0.0.1:8000:8000 `
  -e MCP_PATH=/mcp `
  -v "${PWD}/logs:/srv/logicmcp/logs" `
  -v "${PWD}/output:/srv/logicmcp/output" `
  logicmcp-server
```

直接使用 `docker run` 時，可透過 `-e` 修改 runtime environment，透過 `-p`
修改 port mapping，透過 `-v` 修改持久化路徑。

### 背景執行

```powershell
docker run -d `
  --name logicmcp-server `
  -p 127.0.0.1:8000:8000 `
  -e MCP_PATH=/mcp `
  -v "${PWD}/logs:/srv/logicmcp/logs" `
  -v "${PWD}/output:/srv/logicmcp/output" `
  logicmcp-server
```

停止並移除背景 container：

```powershell
docker stop logicmcp-server
docker rm logicmcp-server
```

## 修改對外位置

例如改成只在本機的 port `9000` 提供 `/logicmcp`：

```dotenv
MCP_PATH=/logicmcp
LOGICMCP_BIND_HOST=127.0.0.1
LOGICMCP_HOST_PORT=9000
```

修改後的 endpoint：

```text
http://127.0.0.1:9000/logicmcp
```

若需要讓區域網路上的 Client 連線，可將 `LOGICMCP_BIND_HOST` 設為
`0.0.0.0`，並另外確認 Windows Firewall 與網路存取政策。

## 修改持久化路徑

相對路徑以 `compose.yaml` 所在的 project directory 為基準，也可以使用絕對路徑：

```dotenv
LOGICMCP_LOG_DIR=D:/LogicMCPData/logs
LOGICMCP_OUTPUT_DIR=D:/LogicMCPData/output
```

修改後重新建立 container：

```powershell
docker compose up -d --force-recreate mcp
```

## 重新建置

修改 `requirements.txt`、`Dockerfile` 或 `server/` 後：

```powershell
docker compose build --no-cache mcp
docker compose up -d mcp
```

只修改 `.env` 或 `compose.yaml` 時不需要重新 build image：

```powershell
docker compose up -d --force-recreate mcp
```

## 清理 image

先停止服務，再確認並移除 image：

```powershell
docker compose down
docker compose images
docker image rm logicmcp-server
```

## 常見問題

### Container 無法啟動

```powershell
docker compose ps
docker compose logs mcp
docker compose config
```

### Host port 已被使用

修改 `.env` 中的 `LOGICMCP_HOST_PORT`，再重新執行 `docker compose up`。

### 修改 `.env` 後沒有生效

執行 `docker compose config --environment` 確認 Compose 讀到的值，再以
`docker compose up -d --force-recreate mcp` 重新建立 container。Shell 中已存在
的同名 environment variable 會優先於 `.env`。

### 找不到 logs 或輸出檔案

確認 `.env` 中的 `LOGICMCP_LOG_DIR`、`LOGICMCP_OUTPUT_DIR` 指向可寫入的
host 目錄，並以 `docker compose config` 檢查解析後的 bind mount source。
