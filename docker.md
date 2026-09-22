# PxDCA — Docker 部署

Docker 是 NAS、Linux Server 與雲端環境的建議部署方式。Image 固定使用
Python 3.13 與 FastMCP 3，並以非 root 使用者執行。

## 啟動

```bash
git clone https://github.com/mydrego-James/PxDCA.git
cd PxDCA
docker compose up --build -d mcp
```

預設 MCP endpoint：

```text
http://127.0.0.1:8000/mcp
```

查看狀態與 logs：

```bash
docker compose ps
docker compose logs -f mcp
```

停止服務但保留資料：

```bash
docker compose down
```

`docker compose down -v` 會同時刪除 session、artifacts 與 logs volumes；除非確定
不再需要資料，否則不要加入 `-v`。

## 外部設定

Compose 將主機的 `config/pxdca.toml` 唯讀掛載到 Container。非機密設定應修改
這個 TOML；`.env` 只負責 Compose 變數或執行環境覆寫。

```dotenv
PXDCA_BIND_HOST=127.0.0.1
PXDCA_HOST_PORT=8000
PXDCA_CONFIG_FILE=./config/pxdca.toml
```

Container 內部路徑：

| 類型 | 路徑 | 說明 |
|---|---|---|
| 設定 | `/srv/pxdca/config/pxdca.toml` | 唯讀掛載 |
| State | `/srv/pxdca/data/state` | session 接續所需的核心資料 |
| Artifacts | `/srv/pxdca/data/artifacts` | 可選的 Markdown／JSON 文件 |
| Logs | `/srv/pxdca/data/logs` | Server 與 HTTP logs |

三種資料分別使用 Docker named volume。需要備份時，可用 Docker volume 備份機制；
如果改用 host bind mount，Linux 主機目錄必須允許容器 UID/GID `10001` 寫入。

## 修改 endpoint

例如只在本機 port `9000` 提供 `/pxdca`：

```toml
# config/pxdca.toml
[server]
host = "0.0.0.0"
port = 8000
path = "/pxdca"
transport = "http"
```

```dotenv
PXDCA_BIND_HOST=127.0.0.1
PXDCA_HOST_PORT=9000
```

重新建立服務：

```bash
docker compose up --build -d mcp
```

新的 endpoint 為 `http://127.0.0.1:9000/pxdca`。

## 不使用 Compose

```bash
docker build -t pxdca-server .
docker run --rm -p 127.0.0.1:8000:8000 \
  -v "$(pwd)/config/pxdca.toml:/srv/pxdca/config/pxdca.toml:ro" \
  pxdca-server
```

正式部署時仍應另外掛載 `/srv/pxdca/data/state`，否則刪除 Container 後無法接續
既有 `session_id`。

## 平台範圍

預設 image 以 Debian slim 為基底，目標平台為 `linux/amd64` 與 `linux/arm64`。
多數現代 NAS 應使用這兩種架構；32-bit `arm/v7` 不列入目前保證範圍。
