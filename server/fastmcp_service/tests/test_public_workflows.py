from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path


_RUNTIME = tempfile.TemporaryDirectory(prefix="pxdca-tests-")
os.environ["PXDCA_ARTIFACT_ROOT"] = str(Path(_RUNTIME.name) / "output")
os.environ["PXDCA_STATE_ROOT"] = str(Path(_RUNTIME.name) / "state")
os.environ["PXDCA_LOG_ROOT"] = str(Path(_RUNTIME.name) / "logs")
os.environ["PXDCA_ALLOW_TOOL_OUTPUT_OVERRIDE"] = "true"

from fastmcp import Client  # noqa: E402

from .. import prompts  # noqa: E402
from ..server import mcp  # noqa: E402
from ..settings import settings  # noqa: E402


def _request(params) -> dict:
    content = params.messages[-1].content
    text = content.text if hasattr(content, "text") else str(content)
    return json.loads(text.split("\n\n前一次輸出")[0])


async def _sampling_handler(messages, params, context) -> str:
    system = params.systemPrompt or ""
    if "optional, context-specific guidance" in system:
        return "### Project convention\n\nPrefer the repository's existing document locations."
    request = _request(params)
    if "Planning Rules" in system:
        for profile_id in (
            "frontend_engineer",
            "backend_engineer",
            "platform_engineer",
            "quality_engineer",
        ):
            if f'"{profile_id}"' not in system:
                raise AssertionError(f"Q0 did not receive capability profile: {profile_id}")
        if "not by implementation language" not in system:
            raise AssertionError("Q0 did not receive the capability granularity rule")
        q0 = request["q0"]
        return json.dumps({
            "schema_version": "2.0", "stage": "consultant_plan",
            "selected_profile": "simple",
            "topic": {"raw": q0, "normalized": q0, "language": "zh-TW"},
            "facts": {},
            "qa_items": [
                _question("Q1", 1, ["purpose", "primary_users"], 10, "frontend_engineer"),
                _question("Q2", 2, ["core_scope", "basic_constraints"], 9, "backend_engineer"),
                _question("Q3", 3, ["acceptance_criteria", "material_assumptions"], 8, "platform_engineer"),
            ],
            "advisory_suggestions": [], "active_question_id": "Q1",
            "converged": False, "reason": "test",
        }, ensure_ascii=False)
    if "Requirement State Semantics" in system:
        state = request["requirement_state"]
        answer = request["user_message"]
        active_id = state["active_question_id"]
        active = next(item for item in state["qa_items"] if item["id"] == active_id)
        expected_profile_markers = {
            "Q1": "Frontend Engineering Architect",
            "Q2": "Backend Engineering Architect",
            "Q3": "Platform and Reliability Architect",
        }
        expected_marker = expected_profile_markers[active_id]
        if expected_marker not in system:
            raise AssertionError(
                f"{active_id} did not load its capability profile prompt: {expected_marker}"
            )
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
        if system.count("[Architecture Capability Boundary - Single Pass]") != 1:
            raise AssertionError("Architecture capability boundary was not injected once")
        if "not as personas or sequential role changes" not in system:
            raise AssertionError("Architecture prompt permits capability role switching")
        for capability_marker in (
            "Frontend Engineering Architect",
            "Backend Engineering Architect",
            "Platform and Reliability Architect",
        ):
            if capability_marker not in system:
                raise AssertionError(
                    "Architecture did not receive capability prompt: "
                    f"{capability_marker}"
                )
        qa_context = request.get("requirement_qa_context")
        expected_routes = [
            ("Q1", "frontend_engineer"),
            ("Q2", "backend_engineer"),
            ("Q3", "platform_engineer"),
        ]
        actual_routes = [
            (item.get("question_id"), item.get("capability_profile"))
            for item in qa_context or []
        ]
        if actual_routes != expected_routes:
            raise AssertionError("Architecture did not receive the first-stage Q&A routing")
        if any(not item.get("answer") for item in qa_context or []):
            raise AssertionError("Architecture did not receive every accepted Q&A answer")
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


def _question(
    question_id: str,
    order: int,
    dimensions: list[str],
    priority: int,
    capability_profile: str,
) -> dict:
    return {
        "id": question_id, "display_order": order, "dimension": question_id,
        "policy_dimensions": dimensions, "capability_profile": capability_profile,
        "target_fact": question_id, "priority": priority, "status": "pending",
        "question": {"type": "fill_in", "text": f"{question_id}?", "options": []},
        "answer": None, "assessment": None, "follow_ups": [], "source_turn": 0,
    }


class PublicWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_artifact_output_is_optional(self) -> None:
        original = settings.artifacts.enabled
        object.__setattr__(settings.artifacts, "enabled", False)
        try:
            async with Client(mcp) as client:
                result = (await client.call_tool("generate_skill", {"mode": "template"})).data
            self.assertEqual(result["status"], "completed")
            self.assertIsNone(result["artifact"])
            self.assertIn("generate_requirements", result["content"])
        finally:
            object.__setattr__(settings.artifacts, "enabled", original)

    async def test_absolute_artifact_destination_is_rejected(self) -> None:
        async with Client(mcp) as client:
            result = (
                await client.call_tool(
                    "generate_skill",
                    {"mode": "template", "output_dir": str(Path(_RUNTIME.name).resolve())},
                )
            ).data
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error"]["code"], "INVALID_OUTPUT_DIR")

    def test_every_registered_capability_profile_loads_its_txt(self) -> None:
        service_root = Path(__file__).resolve().parents[1]
        registry = json.loads(
            (service_root / "resources" / "templates" / "profiles.json").read_text(
                encoding="utf-8"
            )
        )
        for profile_id, profile in registry.items():
            prompt_path = service_root / "prompts" / "profiles" / profile["prompt_file"]
            self.assertTrue(prompt_path.is_file(), profile_id)
            self.assertNotIn(
                "General software requirement analysis",
                prompts.requirement_interview(profile_id),
                profile_id,
            )

        self.assertIn(
            "Quality and Test Engineering Architect",
            prompts.requirement_interview("quality_engineer"),
        )

    async def test_public_contract_is_exactly_four_tools(self) -> None:
        async with Client(mcp) as client:
            tools = await client.list_tools()
            self.assertEqual(
                [tool.name for tool in tools],
                [
                    "generate_requirements",
                    "generate_architecture",
                    "run_audit",
                    "generate_skill",
                ],
            )
            self.assertEqual(await client.list_prompts(), [])
            self.assertEqual(await client.list_resources(), [])
            baseline_path = Path(__file__).resolve().parents[1] / "docs" / "contract-baseline.json"
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            actual = [
                {
                    "name": tool.name,
                    "required": tool.inputSchema.get("required", []),
                    "parameters": list(tool.inputSchema.get("properties", {}).keys()),
                }
                for tool in tools
            ]
            self.assertEqual(actual, baseline["tools"])

    async def test_generate_canonical_and_optimized_skill(self) -> None:
        state_root = Path(os.environ["PXDCA_STATE_ROOT"])
        sessions_before = set(state_root.glob("*.json"))
        async with Client(mcp) as client:
            canonical = (
                await client.call_tool(
                    "generate_skill",
                    {"mode": "template", "output_dir": "skills/canonical"},
                )
            ).data
            self.assertEqual(canonical["status"], "completed")
            self.assertEqual(canonical["mode"], "template")
            canonical_content = canonical["content"]
            canonical_path = Path(canonical["artifact"]["path"])
            self.assertEqual(canonical_path.read_text(encoding="utf-8"), canonical_content)

            required = [
                "Plan",
                "Do",
                "Check",
                "Act",
                "Problem / Purpose",
                "Design",
                "Check / Challenge",
                "Action",
                "generate_requirements",
                "generate_architecture",
                "run_audit",
                "session_id",
            ]
            for item in required:
                self.assertIn(item, canonical_content)

        async with Client(mcp, sampling_handler=_sampling_handler) as client:
            optimized = (
                await client.call_tool(
                    "generate_skill",
                    {
                        "mode": "optimized",
                        "customization": "Follow project document locations.",
                        "output_dir": "skills/optimized",
                    },
                )
            ).data
            self.assertEqual(optimized["status"], "completed")
            self.assertIn(canonical_content.rstrip(), optimized["content"])
            self.assertIn("Project convention", optimized["content"])
            for item in required:
                self.assertIn(item, optimized["content"])
        self.assertEqual(set(state_root.glob("*.json")), sessions_before)

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

        state_path = Path(os.environ["PXDCA_STATE_ROOT"]) / f"{session_id}.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertEqual(state["phase"], "audit_completed")
        self.assertEqual(state["requirement_state"]["turn_count"], 3)


if __name__ == "__main__":
    unittest.main()
