"""Deterministic routing outline for a Client that already has an LLM handler."""

from __future__ import annotations

from fastmcp import Client


ENDPOINT = "http://127.0.0.1:8000/mcp"


async def run_workflow(sampling_handler) -> None:
    # sampling_handler is implemented by the host Client and calls its selected LLM.
    async with Client(ENDPOINT, sampling_handler=sampling_handler) as client:
        started = await client.call_tool(
            "generate_requirements",
            {"q0": "建立一個設備維護管理系統", "profile": "professional"},
        )
        print(started.data)

        session_id = started.data["session_id"]

        # The application can close here. Save session_id in its own project/UI.
        resumed = await client.call_tool(
            "generate_requirements",
            {"session_id": session_id},
        )
        print(resumed.data)

        answered = await client.call_tool(
            "generate_requirements",
            {"session_id": session_id, "answer": "維修主管與現場技師使用。"},
        )
        print(answered.data)

        # Continue the same Tool until status == "completed", then:
        # await client.call_tool("generate_architecture", {"session_id": session_id})
        # await client.call_tool("run_audit", {"session_id": session_id})
# The embedding application calls:
# asyncio.run(run_workflow(its_sampling_handler))
