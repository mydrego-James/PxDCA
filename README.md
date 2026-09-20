# PxDCA

> **Before implementation, align the logic.**
>
> 在任何實作開始之前，先用文字確認需求、技術規劃與交付依據指向同一個方向。

> **改名註記：** 本專案原名為 `LogicMCP_Server`，現已改名為 `PxDCA`。程式內既有的 `LogicMCP`、`LOGICMCP_*` 與 `logicmcp-pdca` 等識別目前為相容性名稱，仍可正常使用。

PxDCA 是以 [FastMCP 3](https://gofastmcp.com/) 建置的文字規劃與邊界校準服務。它不負責撰寫產品程式碼，而是透過 MCP 與背後的 Prompt TXT，讓 AI 以有依據、可追溯且不過度延伸的方式建立需求與技術規劃。前三個公開 MCP Tools 產生需求書、架構書與 PM／PG 對齊報告；第 4 個 Tool 產生可選的 `SKILL.md`。

- `generate_requirements`：建立並接續需求訪談，完成後產生需求書。
- `generate_architecture`：根據已完成的需求工作階段產生技術選型與架構規劃書。
- `run_audit`：以 PQ 視角檢查 PM 需求與 PG 技術規劃的一致性、覆蓋、風險及追溯關係。
- `generate_skill`：輸出 canonical `SKILL.md`，或在不改變核心規則的前提下加入情境化指引。

完整的專案背景、PxDCA 雙軸模型與原 LogicMCP 故事請見 [PxDCA Wiki](https://github.com/mydrego-James/PxDCA/wiki)。

## 1. 故事

AI 已經能快速產生程式碼、文件、架構與測試，軟體開發的瓶頸也因此從「產出速度」轉向「方向校準與邊界控制」。執行越快，方向錯誤、責任越界或任務層級混亂造成的返工成本就越高。

常見問題不是「做不出來」，而是：

- 需求尚未確認，實作就已經開始。
- 需求提出者、開發者與 AI 對目標的理解不同。
- AI 自行補上看似合理、但未經確認的條件。
- 局部功能正確，整體業務邏輯卻偏離原始目的。
- 大型規劃沒有降解成可驗證的小型任務，實作者同時處理全域架構與底層細節。
- 工作分派後，執行者只看到局部任務，遺失上層目標、背景與限制。
- 產出完成後缺乏可證偽的品質門禁，結果「看似完成」卻無法驗證。

PxDCA 的目的不是把 PDCA 寫成一條強制流水線，也不是取代需求提出者、專案經理、架構師或 AI。PDCA 在這裡是一種 AI 必須持續具備的理解力：先掌握現況與目標，再依證據行動；產生結果後重新對照來源，必要時修正、補問或重新規劃。這種精神從 Q0 與 QA 階段就已經開始存在。

PxDCA 中的 `x` 有兩種互相連接的含意：

1. **職務焦點：PM、PG、PQ**

   - `PM`：收集需求、釐清目標與範圍，建立需求規劃文字。
   - `PG`：承接 PM 已確認的內容，建立技術選型與架構規劃文字，不得自行擴增業務需求。
   - `PQ`：對齊 PM 與 PG 的上下依據，檢查技術規劃是否有需求來源、需求是否獲得技術回應，以及缺口應回到哪一端修正。PQ 不是另一個獨立規劃任務。

2. **任務交付展開：`P1 / D1 / C1 / A1 → P2 ...`**

   前一項工作整理出的目標、證據、決策與檢查結果，可以成為下一項工作的輸入。這表示任務之間要有可追溯的交付關係，不表示 MCP Server 必須依序執行一套固定的 PDCA 狀態機。

因此目前的核心關係是：

```text
PM：需求收集與需求規劃文字
          │ 有來源的需求基線
          ▼
PG：技術選型與架構規劃文字
          │ 需求與技術的對應證據
          ▼
PQ：檢查 PM ↔ PG 的上下連接與偏離
```

只有 PM 與 PG 負責產生主要規劃內容；PQ 負責對齊、指出缺口與修正方向。整個過程以文字為產物，以來源、回答、決策與對應關係為證據，避免 AI 自行補充未經授權的需求或技術範圍。

> AI 負責高速推進，PxDCA 負責鎖定邊界與工程方向。

## 2. 安裝

### 2.1 Git／本機安裝

需求：

- Git
- Windows
- Python 3.11 或更新版本

取得專案：

```powershell
git clone https://github.com/mydrego-James/PxDCA.git
cd PxDCA
```

建立本機設定：

```powershell
Copy-Item .env.example .env
```

預設設定如下：

```dotenv
MCP_HOST=127.0.0.1
MCP_PORT=8000
MCP_PATH=/mcp
MCP_TRANSPORT=http
MCP_OUTPUT_ROOT=./output
MCP_STATE_ROOT=./output/.logicmcp/sessions
```

安裝並啟動：

```powershell
.\install.bat
.\run.bat
```

預設 MCP endpoint：

```text
http://127.0.0.1:8000/mcp
```

`MCP_STATE_ROOT` 保存需求訪談狀態。若要在 Client 關閉、隔天或 Server 重啟後繼續，請將它放在持久化磁碟中。

### 2.2 Docker 安裝

需求：Docker Engine；若使用 Compose，需同時安裝 Docker Compose。

```powershell
git clone https://github.com/mydrego-James/PxDCA.git
cd PxDCA
Copy-Item .env.example .env
docker compose up --build -d mcp
```

查看狀態與 logs：

```powershell
docker compose ps
docker compose logs -f mcp
```

停止服務：

```powershell
docker compose down
```

Compose 預設將 `./logs` 與 `./output` 掛載到 Container。需求訪談狀態保存在 `output/.logicmcp/sessions/`，重建 Container 後仍可使用原本的 `session_id` 接續。

若需要修改對外 IP、port 或持久化路徑，可調整 `.env`：

```dotenv
LOGICMCP_BIND_HOST=127.0.0.1
LOGICMCP_HOST_PORT=8000
LOGICMCP_LOG_DIR=./logs
LOGICMCP_OUTPUT_DIR=./output
```

完整設定與 `docker run` 範例請見 [docker.md](docker.md)。

## 3. 使用：VS Code 範例

### 3.1 連接 PxDCA

先啟動 PxDCA Server，然後在要使用它的 VS Code workspace 建立 `.vscode/mcp.json`：

```json
{
  "servers": {
    "pxdca": {
      "type": "http",
      "url": "http://127.0.0.1:8000/mcp"
    }
  }
}
```

接著在 VS Code：

1. 開啟 Command Palette（`Ctrl+Shift+P`）。
2. 執行 `MCP: List Servers`。
3. 啟動 `pxdca`。
4. 在 Chat 的工具清單中確認可看到四個 PxDCA Tools。

VS Code 所使用的 MCP Client 必須支援 MCP Sampling，因為 Server 會在封閉流程中請 Client 的模型執行受控推理。

### 3.2 建立需求書

可以直接在 Chat 中描述目標：

```text
請使用 PxDCA，為「建立一套設備維護管理系統」建立需求書，
使用 professional profile，並逐題向我確認。
```

AI 會呼叫：

```json
{
  "tool": "generate_requirements",
  "arguments": {
    "q0": "建立一套設備維護管理系統",
    "profile": "professional"
  }
}
```

Server 會回傳 `session_id`、目前問題與訪談狀態。回答問題時，AI 會使用同一個 Tool：

```json
{
  "tool": "generate_requirements",
  "arguments": {
    "session_id": "SERVER_RETURNED_SESSION_ID",
    "answer": "由維修主管與現場技師使用。"
  }
}
```

若中斷對話，只要保留 `session_id`，之後可要求：

```text
請使用 session_id「SERVER_RETURNED_SESSION_ID」接續上次的需求訪談。
```

只傳入 `session_id` 時，Server 會讀取上次通過驗證的狀態並回傳目前問題，不會重問已接受的答案。

### 3.3 建立架構書

需求書完成後，在 Chat 中要求：

```text
請使用同一個 PxDCA session 產生架構書。
```

對應呼叫：

```json
{
  "tool": "generate_architecture",
  "arguments": {
    "session_id": "SERVER_RETURNED_SESSION_ID"
  }
}
```

需求階段與技術架構階段共用同一批 `prompts/profiles/*.txt` 能力定義。需求階段可以依問題切換焦點；架構階段則讀取第一階段完整的問題、答案、判定及 `capability_profile`，只進行一次整體焦點對應，再把相關 TXT 合併成單一 AI 技能邊界加入架構 Prompt，不會再次逐題切換身分。兩階段仍使用不同的 Prompt 契約與 Markdown 渲染模板，因此分別產生需求書與架構書，不會把兩種文件混成同一份模板。

### 3.4 執行稽核

架構書完成後，在 Chat 中要求：

```text
請稽核這個 session 的需求書與架構書，列出缺漏、矛盾、風險及追溯結果。
```

對應呼叫：

```json
{
  "tool": "run_audit",
  "arguments": {
    "session_id": "SERVER_RETURNED_SESSION_ID"
  }
}
```

完成的架構與稽核呼叫具冪等性。再次使用相同 `session_id` 時，Server 會回傳既有產物，不會重複生成。

## 4. 目前架構

PxDCA 對 MCP Client 公開三個文字產物操作與一個 Skill 產生工具。MCP Tools 是呼叫介面；真正讓 AI 理解 PM、PG、PQ 邊界與 PDCA 精神的是 Server 內部的 Prompt TXT。Policies、Profiles、Schemas、Validators、狀態轉移與 Renderers 同樣屬於私有實作，不會註冊成額外的 MCP Prompts、Resources 或 Tools。

```text
VS Code／其他 MCP Client
        │
        │ MCP + Client LLM Sampling
        ▼
┌─────────────────────────────────────────────┐
│ PxDCA Server                                │
│                                             │
│  generate_requirements                      │
│  generate_architecture                      │
│  run_audit                                  │
│  generate_skill                             │
│                │                            │
│                ▼                            │
│  Private workflow orchestration             │
│  Prompts / Policies / Schemas / Validators  │
│  State transitions / Renderers              │
└───────────────────┬─────────────────────────┘
                    │
                    ▼
          Persistent session + artifacts
```

### 工作流程

```text
Q0
 ↓
generate_requirements
 ↓ 逐題訪談、驗證並持久化狀態
PM 需求書
 ↓
generate_architecture
 ↓ 承接 PM 證據，進行技術選型與規劃
PG 架構書
 ↓
run_audit
 ↓ 以 PQ 視角對齊 PM 與 PG
對齊與稽核報告
```

MCP 連線本身不是工作狀態。Server 只保存通過驗證的狀態，並以 `session_id` 恢復流程。需求、架構及稽核產物預設位於 `output/<session_id>/`，工作階段位於 `output/.logicmcp/sessions/`，Server logs 位於 `logs/fastmcp/`。`.logicmcp` 是目前保留的相容性目錄名稱。

### 專案結構

```text
server/
├─ entrypoint.py
└─ fastmcp_service/
   ├─ public_tools.py       四個公開 MCP Tools
   ├─ skill_service.py      SKILL.md 產生與可選優化
   ├─ workflow_service.py   工作流程與持久化 session
   ├─ prompts.py            私有 Prompt 讀取與組合
   ├─ prompts/              私有 Prompt templates
   ├─ resources.py          私有 Resource 讀取
   ├─ resources/            Policies、Schemas、Templates
   ├─ tools/                私有 Validators 與 Renderers
   ├─ tests/                公開工作流程測試
   └─ docs/                 契約、邊界與工作流程文件

logs/                       Server runtime logs
output/                     Session 狀態與生成文件
tools/                      維護工具與開發計畫
└─ SKILL.md                 Canonical AI Skill 模板

install.bat                 本機安裝
run.bat                     本機啟動
fastmcp.json                FastMCP filesystem deployment
Dockerfile                  Docker image
compose.yaml                Docker Compose service
```

更完整的檔案索引請見 [MAP.MD](MAP.MD)，輸入輸出邊界請見 [IO_BOUNDARY.md](server/fastmcp_service/docs/IO_BOUNDARY.md)。

## 5. 附加工具：SKILL.md

[tools/SKILL.md](tools/SKILL.md) 是可獨立交給 AI 讀取的 canonical 模板。它以原始 PDCA 精神規範三件事：

1. 讓 AI 分辨原始 `Plan → Do → Check → Act`，以及 PxDCA（原 LogicMCP）在目前 MCP 工作流中的 `Problem/Purpose → Design → Check/Challenge → Action`。
2. 讓 AI 依目前要做的工作，檢查既有需求、規格、規劃及架構內容是否足夠，而不是只看檔名。
3. 當資料不足且使用者同意時，讓 AI 正確使用 `generate_requirements`、`generate_architecture`、`run_audit` 與 `session_id` 接續規則。

Skill 不是持久服務、背景監控器或 MCP 必要依賴。使用者可以直接呼叫 MCP，也可以將 `SKILL.md` 交給 AI 使用。前三個開發工作流不依賴 Skill。

### Skill 不是必要流程

PxDCA 的安裝、啟動及前三個開發工作流都不要求使用 Skill。使用者可以依自己的 IDE、Agent、網路 Chat 或開發習慣選擇：

- 直接呼叫 PxDCA Tools。
- 使用自己編寫的 Prompt 或 Agent 規則。
- 在支援 Skill 的工具中引用 `SKILL.md`。
- 完全不使用 Skill。

`SKILL.md` 只是讓 AI 預先理解兩種 PDCA 的差異、如何判斷目前狀態是否足夠，以及資料不足時如何正確使用 PxDCA MCP Tools。

### 在 AI 工具中載入 Skill

不同 IDE、Coding Agent 與網路 Chat 對 Skill 的支援方式不同，目前沒有所有工具共用的單一安裝或呼叫標準。請以實際使用工具的說明為準。

在支援以名稱呼叫 Skill 的環境中，使用 Skill 自己的名稱即可。這份模板目前仍保留原專案的相容性名稱 `logicmcp-pdca`，因此可在主要任務開始前這樣引用：

```text
/logicmcp-pdca

請根據目前專案狀態，判斷是否已有足夠的需求、規格與架構內容可開始開發。
```

`/logicmcp-pdca` 不是所有平台共用的制式命令，而是以 Skill 名稱呼叫這份模板的示例。若使用者將 frontmatter 的 `name` 改成其他名稱，則應使用 `/<自訂技能名稱>`，例如 `/my-project-pdca`。不同平台也可能透過 Skill 選單、提及、附件或其他介面載入，因此仍應以實際工具的能力為準。

### MCP 與 Skill 的關係

從 AI 取得能力的角度來看，MCP 也可以視為廣義 Skill 的一種；兩者主要差異在能力被放置與載入的位置：

```text
MCP
→ 能力、Tools 與狀態位於本機或雲端 MCP Server
→ AI 透過 MCP protocol 連線並呼叫

SKILL.md
→ 指令與使用知識被引入本地環境或沙盒
→ 支援名稱呼叫時，可使用 /logicmcp-pdca 或 /<自訂技能名稱>
```

在 PxDCA 中，MCP Server 提供可執行的需求、架構、稽核與 Skill 產生能力；`SKILL.md` 則讓 AI 在本地或沙盒上下文中理解兩種 PDCA、判斷目前狀態，以及在必要時正確呼叫 MCP。兩者可以一起使用，也可以依使用者環境分開使用。

若使用的 IDE 或網路 Chat 不支援 Skill，也可以將 `SKILL.md` 上傳、拖入對話或貼入內容，明確要求 LLM 先讀取再處理任務：

```text
請先讀取附加的 SKILL.md，確認其中兩種 PDCA 定義與 PxDCA 使用規則，
再檢查目前專案是否具備足夠的開發基線。
```

直接把 Markdown 放入既有對話不是標準化的 Skill 載入方式。既有對話內容、其他提示及上下文順序都可能影響 LLM 對文件的理解，因此可靠性通常低於平台原生的 Skill 引用方式。重要工作應確認 AI 已正確理解 Skill 的三項責任後再繼續。

第 4 個公開 Tool `generate_skill` 可輸出一份 Skill：

```json
{
  "tool": "generate_skill",
  "arguments": {
    "mode": "template",
    "output_dir": "logicmcp-pdca"
  }
}
```

`template` 模式原樣輸出 canonical 模板。`optimized` 模式可透過 Client LLM Sampling 附加情境化內容：

```json
{
  "tool": "generate_skill",
  "arguments": {
    "mode": "optimized",
    "customization": "加入本專案既有文件位置與命名慣例",
    "output_dir": "logicmcp-pdca-custom"
  }
}
```

情境化內容只能附加，不能覆蓋兩種 PDCA 的差異、前三個開發工具的用途或 `session_id` 規則。`generate_skill` 不建立需求 session。

`generate_skill` 只產生 `SKILL.md` 檔案與回傳內容，不會替任何 IDE、Agent 或 Chat 自動安裝、註冊或啟用 Skill。產生後仍需依使用平台的方式引用：

```text
generate_skill
→ 取得 artifact.path 與 content
→ 安裝到平台指定的 Skill 位置
→ 支援名稱呼叫時，以 /logicmcp-pdca 或 /<自訂技能名稱> 引用
→ 不支援 Skill 時，將 Markdown 明確提供給 LLM
→ AI 讀取後才依 Skill 判斷狀態及選擇是否使用 MCP
```

本機 MCP Client 通常可直接存取 `artifact.path`。若 PxDCA 部署在遠端，該路徑屬於 Server filesystem，Client 應使用 Tool result 中的 `content` 保存或載入 Skill，不應假設能直接開啟 Server 路徑。

## 6. 未來計畫

目前的 PxDCA Server 是一個可執行的文字規劃前哨站：透過 PM 需求收集、PG 技術規劃與 PQ 上下對齊，驗證 AI 是否能持續依據來源工作而不過度延伸。後續方向包括：

1. **驗證與改良可選的 `SKILL.md`**

   以實際 AI 使用案例驗證 AI 是否能理解 PDCA 是持續判斷精神，而不是必須機械執行的工作流水線。

2. **強化 PM 需求證據與邊界**

   讓每項需求都能回到 Q0、QA 回答、已確認假設與使用者授權，避免 AI 將建議自動升格為需求。

3. **強化 PG 技術選型對應**

   讓技術選型、模組責任與架構決策逐項對應 PM 需求；技術規劃只能在需求授權範圍內展開。

4. **強化 PQ 上下對齊**

   PQ 不建立另一份獨立規劃，而是確認 PM 與 PG 的覆蓋、衝突、假設與追溯關係，並指出修正應回到需求端或技術端。

5. **保存任務交付展開的依據**

   保存 `P1 / D1 / C1 / A1 → P2 ...` 之間的目標、證據、決策與交付關係，讓下一項文字規劃知道自己承接了什麼。

6. **擴充 Profiles、Templates、Clients 與部署驗證**

   驗證不同領域的能力 TXT、需求與架構文件模板，以及 VS Code 以外的 MCP Clients、模型與 Agent runtime。

PxDCA 不追求成為程式碼生成器或強制執行的流程引擎。它從可追溯的文字規劃開始，讓 AI 在需求收集、技術選型與上下對齊時都保有 PDCA 精神與邊界意識。

---

GitHub 保存程式碼與版本歷史；PxDCA 保存成果背後的需求、規劃、邊界與檢查邏輯。
