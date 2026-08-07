from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


_RUNTIME = tempfile.TemporaryDirectory(prefix="logicmcp-tests-")
os.environ["MCP_OUTPUT_ROOT"] = str(Path(_RUNTIME.name) / "output")
os.environ["MCP_STATE_ROOT"] = str(Path(_RUNTIME.name) / "state")

from fastmcp import Client  # noqa: E402

from ..server import mcp  # noqa: E402


def _request(params) -> dict:
    content = params.messages[-1].content
    text = content.text if hasattr(content, "text") else str(content)
    return json.loads(text.split("\n\n前一次輸出")[0])


async def _sampling_handler(messages, params, context) -> str:
    system = params.systemPrompt or ""
    request = _request(params)
    if "Planning Rules" in system:
        q0 = request["q0"]
        return json.dumps({
            "schema_version": "2.0", "stage": "consultant_plan",
            "selected_profile": "simple",
            "topic": {"raw": q0, "normalized": q0, "language": "zh-TW"},
            "facts": {},
            "qa_items": [
                _question("Q1", 1, ["purpose", "primary_users"], 10),
                _question("Q2", 2, ["core_scope", "basic_constraints"], 9),
                _question("Q3", 3, ["acceptance_criteria", "material_assumptions"], 8),
            ],
            "advisory_suggestions": [], "active_question_id": "Q1",
            "converged": False, "reason": "test",
        }, ensure_ascii=False)
    if "Requirement State Semantics" in system:
        state = request["requirement_state"]
        answer = request["user_message"]
        active_id = state["active_question_id"]
        active = next(item for item in state["qa_items"] if item["id"] == active_id)
        return json.dumps({
            "schema_version": "2.0", "stage": "consultant_answer_review",
            "active_question_id": active_id,
            "capability_profile": active["capability_profile"],
            "focused_assessment": {
                "status": "answered", "normalized_value": answer,
                "evidence": [answer], "reason_summary": "complete",
            },
            "cross_question_updates": [], "conflicts": [], "follow_up": None,
            "scope_extension_candidates": [],
        }, ensure_ascii=False)
    if "final Requirement Batch Audit" in system:
        state = request["requirement_state"]
        return json.dumps({
            "schema_version": "1.0", "stage": "batch_audit_draft", "status": "draft",
            "source_requirement_session_id": state["source_requirement_session_id"],
            "language": "zh-TW", "project_name": "測試專案",
            "project": {"name": "測試專案", "topic": "測試", "summary": "摘要", "objective": "目標", "target_users": ["使用者"]},
            "scope": {"in_scope": ["核心流程"], "out_of_scope": []},
            "core_requirements": [{"id": "REQ-01", "title": "核心流程", "category": "functional", "description": "系統必須提供核心流程。", "rationale": "滿足目標", "source_boundary": "Q1"}],
            "add_on_services": [], "unresolved_items": [],
        }, ensure_ascii=False)
    if "Technical Alignment Planner" in system:
        requirements = request["requirements"]
        return json.dumps({
            "schema_version": "1.0", "stage": "technical_alignment_draft", "status": "draft",
            "source_requirement_session_id": requirements["source_requirement_session_id"],
            "project": {"name": "測試專案", "purpose": "目標"},
            "requirement_alignment": [{"requirement_id": "REQ-01", "summary": "核心流程", "technical_implications": ["建立服務層"], "architecture_acceptance_criteria": ["元件責任明確"], "coverage_status": "covered", "notes": ""}],
            "architecture_outline": ["Client > MCP > Service"],
            "technical_choices": [{"area": "服務", "proposal": "模組化", "rationale": "可維護", "confidence": "high", "requirement_ids": ["REQ-01"]}],
            "assumptions": [], "unresolved_decisions": [], "limitations": [],
        }, ensure_ascii=False)
    if "Audit Draft Reviewer" in system:
        requirements = request["requirement_specification"]
        return json.dumps({
            "schema_version": "1.0", "stage": "audit_draft", "status": "draft",
            "source_requirement_session_id": requirements["source_requirement_session_id"],
            "project_name": "測試專案", "audit_basis": ["requirements", "architecture"],
            "coverage": [{"requirement_id": "REQ-01", "status": "covered", "evidence": ["architecture"], "gap": ""}],
            "findings": [{"finding_id": "AUD-001", "type": "traceability", "severity": "observation", "description": "完整", "recommendation": "維持", "requirement_ids": ["REQ-01"]}],
            "blockers": [], "conclusion": "draft_ready_for_review", "limitations": [],
        }, ensure_ascii=False)
    raise AssertionError("unexpected sampling stage")


def _question(question_id: str, order: int, dimensions: list[str], priority: int) -> dict:
    return {
        "id": question_id, "display_order": order, "dimension": question_id,
        "policy_dimensions": dimensions, "capability_profile": "desktop_app",
        "target_fact": question_id, "priority": priority, "status": "pending",
        "question": {"type": "fill_in", "text": f"{question_id}?", "options": []},
        "answer": None, "assessment": None, "follow_ups": [], "source_turn": 0,
    }


class PublicWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_contract_is_exactly_three_tools(self) -> None:
        async with Client(mcp) as client:
            self.assertEqual(
                [tool.name for tool in await client.list_tools()],
                ["generate_requirements", "generate_architecture", "run_audit"],
            )
            self.assertEqual(await client.list_prompts(), [])
            self.assertEqual(await client.list_resources(), [])

    async def test_persistent_resume_and_complete_pipeline(self) -> None:
        async with Client(mcp, sampling_handler=_sampling_handler) as client:
            started = (await client.call_tool("generate_requirements", {"q0": "測試", "profile": "simple"})).data
            session_id = started["session_id"]
            self.assertEqual(started["current_question"]["id"], "Q1")
            answered = (await client.call_tool("generate_requirements", {"session_id": session_id, "answer": "A1"})).data
            self.assertEqual(answered["current_question"]["id"], "Q2")

        async with Client(mcp, sampling_handler=_sampling_handler) as client:
            resumed = (await client.call_tool("generate_requirements", {"session_id": session_id})).data
            self.assertEqual(resumed["current_question"]["id"], "Q2")
            await client.call_tool("generate_requirements", {"session_id": session_id, "answer": "A2"})
            completed = (await client.call_tool("generate_requirements", {"session_id": session_id, "answer": "A3"})).data
            self.assertEqual(completed["status"], "completed")
            architecture = (await client.call_tool("generate_architecture", {"session_id": session_id})).data
            self.assertEqual(architecture["status"], "completed")
            audit = (await client.call_tool("run_audit", {"session_id": session_id})).data
            self.assertEqual(audit["conclusion"], "draft_ready_for_review")

        state_path = Path(os.environ["MCP_STATE_ROOT"]) / f"{session_id}.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["phase"], "audit_completed")
        self.assertEqual(state["requirement_state"]["turn_count"], 3)


if __name__ == "__main__":
    unittest.main()
