# PxDCA Server 維護工具開發計畫

## 邊界

```text
tools/                         Server repository maintenance
server/fastmcp_service/tools/ MCP protocol Tools
```

根目錄維護工具只從 repository 外部檢查或管理 Server，不由 `server/` import，
也不成為 Server runtime dependency。所有具寫入能力的操作預設採 dry-run，且必須
顯示明確目標。

## 預定結構

```text
tools/
├─ README.md
├─ PLAN.md
├─ doctor.py                  本機環境與設定診斷
├─ contract_check.py          MCP initialize/list/call 與 baseline 比對
├─ runtime_inspect.py         logs/output 摘要與異常檢查
├─ backup.py                  Server 與部署檔備份
├─ update_baseline.py         公開 MCP 契約差異與受控更新
└─ tests/
   ├─ test_doctor.py
   ├─ test_contract_check.py
   ├─ test_runtime_inspect.py
   ├─ test_backup.py
   └─ test_update_baseline.py
```

## Phase 1 — `doctor.py`

檢查項目：

- Python 版本與 `.venv` 狀態。
- `requirements.txt` 中必要套件是否可 import。
- `.env` 必要欄位、port 格式與 output path。
- `fastmcp.json` JSON 格式及其 entrypoint、requirements path 是否存在。
- `compose.yaml` 能否由 `docker compose config` 解析。
- `data/state/`、`data/artifacts/`、`data/logs/` 是否可依設定寫入。
- 指定 MCP port 是否已被其他 process 使用。

介面：

```powershell
.\.venv\Scripts\python.exe tools\doctor.py
.\.venv\Scripts\python.exe tools\doctor.py --json
```

驗收：read-only 執行、exit code 可供 CI 使用、文字與 JSON 結果包含相同 checks。

## Phase 2 — `contract_check.py`

檢查項目：

- 連線並完成 MCP initialize。
- 列出 Tools、Prompts、Resources，確認公開面固定為 3 / 0 / 0。
- 與 `server/fastmcp_service/docs/contract-baseline.json` 比較名稱及 required arguments。
- 驗證 `generate_requirements` 缺少 Q0 時回傳受控錯誤。
- 可選 `--sampling-probe` 使用測試 Sampling handler 建立暫存需求 session，驗證中斷後接續。

介面：

```powershell
.\.venv\Scripts\python.exe tools\contract_check.py --url http://127.0.0.1:8000/mcp
.\.venv\Scripts\python.exe tools\contract_check.py --url http://127.0.0.1:8000/mcp --sampling-probe
```

驗收：initialize/list/call 任一步失敗均回傳非零 exit code；契約差異逐項顯示，
不自動修改 baseline。

## Phase 3 — `runtime_inspect.py`

檢查項目：

- `data/logs/mcps-*.log` 與 `http-*.log` 的檔案數、時間範圍及 error/warning 數量。
- MCP initialize/list/call 對應的 HTTP status。
- Tool started/finished 是否成對。
- `data/artifacts/` 新增檔案的 path、size、modified time 與 SHA-256。
- Credential、Authorization header、request/response body 意外落盤的 pattern scan。

介面：

```powershell
.\.venv\Scripts\python.exe tools\runtime_inspect.py
.\.venv\Scripts\python.exe tools\runtime_inspect.py --since 2026-08-05T00:00:00 --json
```

驗收：只讀取 runtime data，不顯示疑似 secret 的原文；掃描結果可定位到檔名與行號。

## Phase 4 — `backup.py`

預設備份內容：

```text
server/
tools/
requirements.txt
fastmcp.json
Dockerfile
compose.yaml
install.bat
run.bat
README.md
docker.md
MAP.MD
```

預設排除：

```text
.git/
.env
.venv/
logs/
data/
__pycache__/
credentials
```

介面：

```powershell
.\.venv\Scripts\python.exe tools\backup.py --destination D:\PxDCABackup --dry-run
.\.venv\Scripts\python.exe tools\backup.py --destination D:\PxDCABackup --execute
```

驗收：輸出 archive manifest 與 SHA-256；目的地已存在時不覆寫；任何 resolved path
超出 repository 或指定 destination 時立即停止。

## Phase 5 — `update_baseline.py`

流程：

```text
MCP endpoint
> initialize/list
> load contract-baseline.json
> normalized diff
> review report
> explicit --write
> atomic baseline replacement
```

介面：

```powershell
.\.venv\Scripts\python.exe tools\update_baseline.py --url http://127.0.0.1:8000/mcp
.\.venv\Scripts\python.exe tools\update_baseline.py --url http://127.0.0.1:8000/mcp --write
```

驗收：預設只產生 diff；`--write` 前必須先通過 initialize/list；輸出穩定排序；失敗時
保留原 baseline。

## 共用品質要求

- Python 3.12 或 3.13，Windows PowerShell 可直接執行。
- CLI 使用 `argparse`，成功為 exit code `0`，檢查失敗為非零。
- 路徑一律從 repository root resolve，不依賴目前 shell directory。
- 不讀取或輸出 `.env` value；只檢查必要 key 是否存在及格式。
- 不修改 `server/`；唯一例外是經明確 `--write` 核准的 contract baseline 更新。
- 所有檔案寫入採 temporary file 加 atomic replace。
- 單元測試不得啟動外部 LLM 或依賴網路服務。

## 開發順序

```text
doctor.py
> contract_check.py
> runtime_inspect.py
> backup.py
> update_baseline.py
> Windows + Docker integration test
```

每個 Phase 個別提交；下一階段開始前，前一階段的單元測試與 CLI smoke test 必須通過。
