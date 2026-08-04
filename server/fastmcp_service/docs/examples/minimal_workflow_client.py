import asyncio
import json

# -------------------------------------------------------------------------
# 開源整合典範 (Open-Source Integration Example)
#
# 這是一份極簡架構的 Python 狀態機示範，教導未來的開發者如何正確串接 LogicMCP。
# 請勿讓 LLM 自行決定工作流的順序（那會導致黑箱與幻覺），
# 請利用類似本範例的程式碼，強制作為「大腦(LLM)」與「雙手(MCP)」之間的協調者。
# -------------------------------------------------------------------------

async def pseudo_llm_generate(system_prompt: str, user_input: str) -> str:
    """
    虛擬的 LLM 呼叫函式。
    在實際專案中，你可以替換成 openai.ChatCompletion 或 anthropic.messages.create。
    """
    print(f"[LLM] Thinking based on system prompt ({len(system_prompt)} bytes)...")
    # 這裡假設 LLM 回傳了符合 MCP 要求格式的 JSON 字串
    return '{"dummy": "response"}'

async def mcp_get_prompt(prompt_name: str) -> str:
    """虛擬的 MCP 取得 Prompt 函式 (透過 SSE 或 stdio 連線 FastMCP)"""
    return f"You are an expert for {prompt_name}..."

async def mcp_call_tool(tool_name: str, arguments: dict) -> dict:
    """虛擬的 MCP 呼叫 Tool 函式 (將 LLM 的 JSON 輸出丟給 MCP 進行硬性驗證或渲染)"""
    return {"valid": True, "output": "success"}

async def run_phase_1_core_elicitation():
    """
    第一階段：需求收斂 (Phase 1)
    展示 USER UI --> MCP --> PROMPT + USER TEXT --> LLM 的無狀態迴圈
    """
    print("\n=== [Phase 1] 需求收斂階段 ===")

    # 1. 取得面試官的系統設定 (System Prompt)
    system_prompt = await mcp_get_prompt("requirement_interview")

    # 2. 模擬多輪問答的狀態機
    converged = False
    turn = 0
    state_json = "{}" # 初始狀態

    while not converged and turn < 5:
        user_text = input(f"[User UI] 請輸入您的需求 (Turn {turn+1}): ")

        # 將狀態與使用者的回答組合
        context = f"Current State: {state_json}\nUser: {user_text}"

        # 呼叫 LLM 進行推理 (黑箱操作)
        llm_response_json = await pseudo_llm_generate(system_prompt, context)

        # 將 LLM 的輸出丟給 MCP Tool 進行硬性驗證 (白箱防呆)
        validation_result = await mcp_call_tool("validate_requirement_interview_step", {"payload": llm_response_json})

        if validation_result.get("valid"):
            print("[MCP] 驗證成功，更新狀態！")
            # 假設 LLM 判定已經收斂 (converged: true)
            # converged = json.loads(llm_response_json).get("converged", False)
            converged = True # 這裡直接模擬跳出
        else:
            print("[MCP] 驗證失敗，要求 LLM 修正格式...")

        turn += 1

    print("[System] 需求收斂完成！產出 MD 1 (Requirement) 與 MD 2 (Planning)。")
    return "session_xyz_123"

async def run_phase_2_document_workflow(session_id: str):
    """
    第二階段：文件與稽核流程 (Phase 2)
    展示 LOAD MD --> MCP Prompt --> LLM --> MCP Tool --> Render MD
    """
    print(f"\n=== [Phase 2] 文件與稽核流程 (Session: {session_id}) ===")

    # 1. 從磁碟或資料庫讀取第一階段產出的兩份 MD
    print(f"[System] 讀取 {session_id} 的 MD 1 (需求) 與 MD 2 (規劃)...")
    req_md = "# 需求規格書..."
    plan_md = "# 規劃規格書..."

    # 2. Python 取得 ISO 稽核 Prompt；工作流順序仍由 Python 控制
    iso_prompt = await mcp_get_prompt("iso_audit_draft")

    # 3. 將兩份 MD 餵給 LLM 稽核員
    print("[LLM] ISO 稽核員開始審查兩份 MD 之間的落差...")
    audit_json = await pseudo_llm_generate(iso_prompt, f"{req_md}\n\n{plan_md}")

    # 4. 呼叫 MCP Tool 將 LLM 的 JSON 渲染成實體的 MD 3 稽核報告
    print("[MCP] 驗證稽核 JSON 並渲染出 MD 3 報告...")
    await mcp_call_tool("validate_audit_draft", {"payload": audit_json})
    await mcp_call_tool("render_iso_aligned_audit", {"payload": audit_json, "session_id": session_id})

    print("[System] 第二階段完成！後續可依此模式繼續呼叫 MD 4 (主程序員) 與 MD 5 (PM合約)。")

async def main():
    # 狀態機主幹由 Python 掌控，絕不交由 LLM 自行決定下一步！
    session_id = await run_phase_1_core_elicitation()
    await run_phase_2_document_workflow(session_id)

if __name__ == "__main__":
    asyncio.run(main())
