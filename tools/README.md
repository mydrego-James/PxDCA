# PxDCA Maintenance Tools

本目錄保留給 PxDCA Server 的檢視、診斷、契約檢查、備份與更新工具。

這裡的維護工具不會直接註冊為 MCP Tool。`SKILL.md` 是可獨立交給 AI 使用的
canonical 模板，也會由公開的 `generate_skill` Tool 讀取並輸出給使用者。
MCP 註冊入口位於 `server/fastmcp_service/public_tools.py`。

開發範圍、階段與驗收條件見 [PLAN.md](PLAN.md)。
