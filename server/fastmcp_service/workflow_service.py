"""Private, persistent workflow orchestration for PxDCA's public Tools."""

from __future__ import annotations

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from fastmcp import Context

from . import prompts
from .mcp_instance import OUTPUT_ROOT, STATE_ROOT, logger
from .settings import settings
from .tools.audit_renderer import render_audit
from .tools.baseline_renderer import render_planning_spec, render_requirement_spec
from .tools.draft_validator import (
    validate_audit_draft,
    validate_batch_audit_draft,
    validate_technical_alignment_draft,
)
from .tools.requirement_validator import (
    validate_consultant_answer_review,
    validate_consultant_plan,
)


SESSION_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
PROFILE_IDS = {"simple", "professional", "consultant"}
ROOT = Path(__file__).resolve().parent
_SESSION_LOCKS: dict[str, asyncio.Lock] = {}
_LOCKS_GUARD = asyncio.Lock()


class WorkflowError(RuntimeError):
    def __init__(self, code: str, message: str, *, recoverable: bool = True):
        super().__init__(message)
        self.code = code
        self.recoverable = recoverable


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _session_lock(session_id: str) -> asyncio.Lock:
    async with _LOCKS_GUARD:
        return _SESSION_LOCKS.setdefault(session_id, asyncio.Lock())


def _session_path(session_id: str) -> Path:
    if not SESSION_ID_PATTERN.fullmatch(session_id):
        raise WorkflowError("INVALID_SESSION_ID", "session_id 格式不正確。", recoverable=False)
    return STATE_ROOT / f"{session_id}.json"


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
    )
    temporary.replace(path)


def _load_session(session_id: str) -> dict[str, Any]:
    path = _session_path(session_id)
    if not path.exists():
        raise WorkflowError("SESSION_NOT_FOUND", "找不到指定的需求工作階段。", recoverable=False)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkflowError("SESSION_UNREADABLE", "需求工作階段無法讀取。") from error
    if not isinstance(value, dict) or value.get("session_id") != session_id:
        raise WorkflowError("SESSION_INVALID", "需求工作階段內容無效。", recoverable=False)
    return value


def _save_session(session: dict[str, Any]) -> None:
    session["updated_at"] = _now()
    _atomic_write_json(_session_path(str(session["session_id"])), session)


def _resolve_output_dir(value: str, session_id: str) -> Path:
    if value.strip() and not settings.artifacts.allow_tool_override:
        raise WorkflowError(
            "OUTPUT_OVERRIDE_DISABLED",
            "output_dir 已由 PxDCA 外部設定管理；如需開放 Tool 覆寫，請設定 allow_tool_override。",
            recoverable=False,
        )
    requested = Path(value.strip()) if value.strip() else Path(session_id)
    if requested.is_absolute():
        raise WorkflowError(
            "INVALID_OUTPUT_DIR",
            "output_dir 不可使用絕對路徑。",
            recoverable=False,
        )
    resolved = (OUTPUT_ROOT / requested).resolve()
    if resolved != OUTPUT_ROOT and OUTPUT_ROOT not in resolved.parents:
        raise WorkflowError(
            "INVALID_OUTPUT_DIR",
            "相對 output_dir 必須位於 PxDCA artifact root 之內。",
            recoverable=False,
        )
    if settings.artifacts.enabled:
        resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _templates_json() -> str:
    path = ROOT / "resources" / "templates" / "profiles.json"
    return path.read_text(encoding="utf-8")


def _capability_profile_ids() -> set[str]:
    profiles = json.loads(_templates_json())
    return set(profiles) if isinstance(profiles, dict) else set()


def _session_capability_routing(session: dict[str, Any]) -> list[dict[str, str]]:
    requirement_state = session.get("requirement_state")
    if not isinstance(requirement_state, dict):
        return []
    qa_items = requirement_state.get("qa_items")
    if not isinstance(qa_items, list):
        return []
    return [
        {
            "question_id": str(item["id"]),
            "capability_profile": str(item["capability_profile"]),
        }
        for item in qa_items
        if isinstance(item, dict)
        and isinstance(item.get("id"), str)
        and item["id"].strip()
        and isinstance(item.get("capability_profile"), str)
        and item["capability_profile"].strip()
    ]


def _session_capability_profiles(session: dict[str, Any]) -> list[str]:
    profiles = [
        route["capability_profile"]
        for route in _session_capability_routing(session)
    ]
    return list(dict.fromkeys(profiles))


def _requirement_qa_context(session: dict[str, Any]) -> list[dict[str, Any]]:
    requirement_state = session.get("requirement_state")
    if not isinstance(requirement_state, dict):
        return []
    qa_items = requirement_state.get("qa_items")
    if not isinstance(qa_items, list):
        return []
    context: list[dict[str, Any]] = []
    for item in qa_items:
        if not isinstance(item, dict):
            continue
        question = item.get("question")
        context.append(
            {
                "question_id": item.get("id"),
                "capability_profile": item.get("capability_profile"),
                "question": question.get("text") if isinstance(question, dict) else None,
                "answer": item.get("answer"),
                "assessment": item.get("assessment"),
            }
        )
    return context


def _append_validation_errors(
    validation: dict[str, Any], errors: list[str]
) -> dict[str, Any]:
    if not errors:
        return validation
    combined = dict(validation)
    combined["errors"] = [*validation.get("errors", []), *errors]
    combined["valid"] = False
    return combined


def _validate_discovery(
    payload: dict[str, Any], *, q0: str, profile: str
) -> dict[str, Any]:
    validation = validate_consultant_plan(payload)
    errors: list[str] = []
    if payload.get("selected_profile") != profile:
        errors.append("selected_profile must exactly match the requested profile")
    topic = payload.get("topic") if isinstance(payload.get("topic"), dict) else {}
    if topic.get("raw") != q0:
        errors.append("topic.raw must exactly preserve q0")
    known_capabilities = _capability_profile_ids()
    qa_items = payload.get("qa_items")
    if isinstance(qa_items, list):
        for index, item in enumerate(qa_items):
            if not isinstance(item, dict):
                continue
            capability = item.get("capability_profile")
            if capability not in known_capabilities:
                errors.append(
                    f"qa_items[{index}].capability_profile must exactly match "
                    "an Available capability profiles JSON key"
                )
    return _append_validation_errors(validation, errors)


def _validate_requirement_document(
    payload: dict[str, Any], *, session_id: str
) -> dict[str, Any]:
    validation = validate_batch_audit_draft(payload)
    errors: list[str] = []
    if payload.get("source_requirement_session_id") != session_id:
        errors.append("source_requirement_session_id must match the workflow session_id")
    requirement_ids = [
        item.get("id") for item in payload.get("core_requirements", [])
        if isinstance(item, dict)
    ]
    if len(requirement_ids) != len(set(requirement_ids)):
        errors.append("core requirement ids must be unique")
    return _append_validation_errors(validation, errors)


def _validate_architecture_document(
    payload: dict[str, Any], *, requirements: dict[str, Any], session_id: str
) -> dict[str, Any]:
    validation = validate_technical_alignment_draft(payload)
    errors: list[str] = []
    if payload.get("source_requirement_session_id") != session_id:
        errors.append("source_requirement_session_id must match the workflow session_id")
    requirement_ids = {
        item.get("id") for item in requirements.get("core_requirements", [])
        if isinstance(item, dict) and item.get("id")
    }
    alignment_ids = [
        item.get("requirement_id") for item in payload.get("requirement_alignment", [])
        if isinstance(item, dict)
    ]
    if len(alignment_ids) != len(set(alignment_ids)):
        errors.append("requirement_alignment must not contain duplicate requirement ids")
    missing = requirement_ids - set(alignment_ids)
    unknown = set(alignment_ids) - requirement_ids
    if missing:
        errors.append("architecture omitted requirement ids: " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("architecture contains unknown requirement ids: " + ", ".join(sorted(unknown)))
    return _append_validation_errors(validation, errors)


def _validate_audit_document(
    payload: dict[str, Any], *, requirements: dict[str, Any], session_id: str
) -> dict[str, Any]:
    validation = validate_audit_draft(payload)
    errors: list[str] = []
    if payload.get("source_requirement_session_id") != session_id:
        errors.append("source_requirement_session_id must match the workflow session_id")
    requirement_ids = {
        item.get("id") for item in requirements.get("core_requirements", [])
        if isinstance(item, dict) and item.get("id")
    }
    coverage_ids = [
        item.get("requirement_id") for item in payload.get("coverage", [])
        if isinstance(item, dict)
    ]
    if len(coverage_ids) != len(set(coverage_ids)):
        errors.append("audit coverage must not contain duplicate requirement ids")
    missing = requirement_ids - set(coverage_ids)
    unknown = set(coverage_ids) - requirement_ids
    if missing:
        errors.append("audit omitted requirement ids: " + ", ".join(sorted(missing)))
    if unknown:
        errors.append("audit contains unknown requirement ids: " + ", ".join(sorted(unknown)))
    cited_ids = {
        requirement_id
        for finding in payload.get("findings", [])
        if isinstance(finding, dict)
        for requirement_id in finding.get("requirement_ids", [])
    }
    unknown_citations = cited_ids - requirement_ids
    if unknown_citations:
        errors.append(
            "audit findings cite unknown requirement ids: "
            + ", ".join(sorted(unknown_citations))
        )
    return _append_validation_errors(validation, errors)


def _extract_json(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError as error:
        raise WorkflowError("INVALID_LLM_RESPONSE", "Client LLM 未回傳有效 JSON。") from error
    if not isinstance(value, dict):
        raise WorkflowError("INVALID_LLM_RESPONSE", "Client LLM 回傳值必須是 JSON object。")
    return value


async def _sample_validated(
    ctx: Context,
    *,
    stage: str,
    system_prompt: str,
    input_value: dict[str, Any],
    validator: Callable[[dict[str, Any]], dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    request = json.dumps(input_value, ensure_ascii=False, separators=(",", ":"))
    validation: dict[str, Any] = {}
    for attempt in range(1, 3):
        message = request
        if validation:
            message += (
                "\n\n前一次輸出未通過 Server 驗證。請修正後重新輸出完整 JSON：\n"
                + json.dumps(validation.get("errors", []), ensure_ascii=False)
            )
        logger.info("[WORKFLOW SAMPLE] stage=%s attempt=%s", stage, attempt)
        try:
            sampled = await ctx.sample(
                message,
                system_prompt=system_prompt,
                temperature=0.1,
                max_tokens=8192,
            )
        except Exception as error:
            logger.warning("Client sampling failed at stage=%s: %s", stage, error)
            raise WorkflowError(
                "CLIENT_SAMPLING_REQUIRED",
                "此流程需要 MCP Client 支援 Sampling，或由 Client 提供可用的 LLM Sampling handler。",
            ) from error
        try:
            payload = _extract_json(sampled.text)
        except WorkflowError as error:
            validation = {"valid": False, "errors": [str(error)]}
            continue
        validation = validator(payload)
        if validation.get("valid"):
            return payload, validation
        logger.warning(
            "Workflow validation rejected stage=%s errors=%s",
            stage,
            validation.get("errors", []),
        )
    raise WorkflowError(
        "WORKFLOW_VALIDATION_FAILED",
        f"{stage} 經兩次生成後仍未通過 Server 驗證。",
    )


def _question_view(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if not item:
        return None
    question = item.get("question") if isinstance(item.get("question"), dict) else {}
    return {
        "id": item.get("id"),
        "display_order": item.get("display_order"),
        "dimension": item.get("dimension"),
        "status": item.get("status"),
        "text": question.get("text"),
        "type": question.get("type"),
        "options": question.get("options", []),
    }


def _requirement_result(session: dict[str, Any], *, include_questions: bool = False) -> dict[str, Any]:
    state = session.get("requirement_state", {})
    qa_items = state.get("qa_items", []) if isinstance(state, dict) else []
    by_id = {
        item.get("id"): item for item in qa_items if isinstance(item, dict) and item.get("id")
    }
    active = by_id.get(state.get("active_question_id"))
    completed = isinstance(session.get("requirement_document"), dict)
    result: dict[str, Any] = {
        "status": "completed" if completed else "needs_input",
        "workflow": "requirements",
        "session_id": session["session_id"],
        "phase": session.get("phase"),
        "current_question": _question_view(active),
        "answered_count": sum(
            1 for item in qa_items if isinstance(item, dict) and item.get("status") not in {
                "pending", "answer_received", "partially_answered", "needs_clarification",
                "confirmation_required", "conflict",
            }
        ),
        "question_count": len(qa_items),
        "artifacts": session.get("artifacts", {}).get("requirements", []),
        "document": session.get("requirement_document") if completed else None,
        "updated_at": session.get("updated_at"),
    }
    if include_questions:
        result["questions"] = [_question_view(item) for item in qa_items if isinstance(item, dict)]
    return result


def _error_result(workflow: str, error: WorkflowError, session_id: str = "") -> dict[str, Any]:
    return {
        "status": "failed",
        "workflow": workflow,
        "session_id": session_id or None,
        "error": {"code": error.code, "message": str(error), "recoverable": error.recoverable},
    }


async def requirements_workflow(
    ctx: Context,
    *,
    q0: str,
    session_id: str,
    answer: str,
    profile: str,
    output_dir: str,
) -> dict[str, Any]:
    try:
        if session_id:
            lock = await _session_lock(session_id)
            async with lock:
                session = _load_session(session_id)
                if session.get("workflow") != "requirements":
                    raise WorkflowError("SESSION_TYPE_MISMATCH", "這不是需求工作階段。", recoverable=False)
                return await _continue_requirements(ctx, session, answer)

        if not q0.strip():
            raise WorkflowError("Q0_REQUIRED", "建立需求工作階段時必須提供 q0。", recoverable=False)
        if answer.strip():
            raise WorkflowError(
                "SESSION_ID_REQUIRED", "提交 answer 時必須同時提供 session_id。", recoverable=False
            )
        if profile not in PROFILE_IDS:
            raise WorkflowError("INVALID_PROFILE", "profile 必須是 simple、professional 或 consultant。", recoverable=False)

        new_id = uuid.uuid4().hex
        lock = await _session_lock(new_id)
        async with lock:
            prompt = prompts.discovery_prompt(_templates_json())
            _, validation = await _sample_validated(
                ctx,
                stage="consultant_plan",
                system_prompt=prompt,
                input_value={"q0": q0.strip(), "selected_profile": profile},
                validator=lambda payload: _validate_discovery(
                    payload, q0=q0.strip(), profile=profile
                ),
            )
            state = validation["new_state"]
            state["source_requirement_session_id"] = new_id
            now = _now()
            session = {
                "schema_version": "1.0",
                "session_id": new_id,
                "workflow": "requirements",
                "phase": "interviewing" if not state.get("converged") else "requirements_ready",
                "profile": profile,
                "output_dir": str(_resolve_output_dir(output_dir, new_id)),
                "created_at": now,
                "updated_at": now,
                "requirement_state": state,
                "artifacts": {},
            }
            _save_session(session)
            if state.get("converged"):
                return await _finalize_requirements(ctx, session)
            return _requirement_result(session, include_questions=True)
    except WorkflowError as error:
        return _error_result("requirements", error, session_id)


async def _continue_requirements(
    ctx: Context, session: dict[str, Any], answer: str
) -> dict[str, Any]:
    if isinstance(session.get("requirement_document"), dict):
        return _requirement_result(session, include_questions=True)
    state = session["requirement_state"]
    if state.get("converged"):
        return await _finalize_requirements(ctx, session)
    if not answer.strip():
        return _requirement_result(session, include_questions=True)

    active_id = state.get("active_question_id")
    active_item = next(
        (item for item in state.get("qa_items", []) if item.get("id") == active_id), None
    )
    if not active_item:
        raise WorkflowError("ACTIVE_QUESTION_MISSING", "工作階段缺少待回答問題。")
    prompt = prompts.requirement_interview(str(active_item.get("capability_profile", "")))
    _, validation = await _sample_validated(
        ctx,
        stage="consultant_answer_review",
        system_prompt=prompt,
        input_value={"requirement_state": state, "user_message": answer},
        validator=lambda payload: validate_consultant_answer_review(
            payload, user_message=answer, requirement_state=state
        ),
    )
    session["requirement_state"] = validation["new_state"]
    session["requirement_state"]["source_requirement_session_id"] = session["session_id"]
    session["phase"] = (
        "requirements_ready" if session["requirement_state"].get("converged") else "interviewing"
    )
    _save_session(session)
    if session["requirement_state"].get("converged"):
        return await _finalize_requirements(ctx, session)
    return _requirement_result(session, include_questions=True)


async def _finalize_requirements(ctx: Context, session: dict[str, Any]) -> dict[str, Any]:
    payload, _ = await _sample_validated(
        ctx,
        stage="batch_audit_draft",
        system_prompt=prompts.batch_audit_draft(session["profile"]),
        input_value={"requirement_state": session["requirement_state"]},
        validator=lambda candidate: _validate_requirement_document(
            candidate, session_id=session["session_id"]
        ),
    )
    session["requirement_document"] = payload
    artifacts: list[dict[str, Any]] = []
    if settings.artifacts.enabled:
        output_dir = Path(session["output_dir"])
        json_path = output_dir / "requirements.json"
        _atomic_write_json(json_path, payload)
        rendered = render_requirement_spec(payload, output_dir / "requirement-spec.md")
        artifacts = [
            {"kind": "requirements_json", "path": str(json_path)},
            {"kind": "requirement_specification", **rendered},
        ]
    session.setdefault("artifacts", {})["requirements"] = artifacts
    session["phase"] = "requirements_completed"
    _save_session(session)
    return _requirement_result(session, include_questions=True)


async def architecture_workflow(
    ctx: Context, *, session_id: str, output_dir: str
) -> dict[str, Any]:
    try:
        lock = await _session_lock(session_id)
        async with lock:
            session = _load_session(session_id)
            requirements = session.get("requirement_document")
            if not isinstance(requirements, dict):
                raise WorkflowError(
                    "REQUIREMENTS_NOT_COMPLETED",
                    "必須先完成同一個 session_id 的需求書。",
                    recoverable=False,
                )
            existing_document = session.get("architecture_document")
            existing = session.get("artifacts", {}).get("architecture", [])
            if isinstance(existing_document, dict):
                return {
                    "status": "completed", "workflow": "architecture",
                    "session_id": session_id, "artifacts": existing,
                    "document": existing_document,
                }
            target = _resolve_output_dir(output_dir, session_id) if output_dir.strip() else Path(session["output_dir"])
            payload, _ = await _sample_validated(
                ctx,
                stage="technical_alignment_draft",
                system_prompt=prompts.technical_alignment_draft(
                    session["profile"], _session_capability_profiles(session)
                ),
                input_value={
                    "requirements": requirements,
                    "requirement_qa_context": _requirement_qa_context(session),
                },
                validator=lambda candidate: _validate_architecture_document(
                    candidate, requirements=requirements, session_id=session_id
                ),
            )
            artifacts: list[dict[str, Any]] = []
            if settings.artifacts.enabled:
                target.mkdir(parents=True, exist_ok=True)
                json_path = target / "architecture.json"
                _atomic_write_json(json_path, payload)
                rendered = render_planning_spec(payload, target / "architecture.md")
                artifacts = [
                    {"kind": "architecture_json", "path": str(json_path)},
                    {"kind": "architecture_document", **rendered},
                ]
            session["architecture_document"] = payload
            session.setdefault("artifacts", {})["architecture"] = artifacts
            session["phase"] = "architecture_completed"
            _save_session(session)
            return {
                "status": "completed", "workflow": "architecture",
                "session_id": session_id, "artifacts": artifacts, "document": payload,
            }
    except WorkflowError as error:
        return _error_result("architecture", error, session_id)


async def audit_workflow(ctx: Context, *, session_id: str, output_dir: str) -> dict[str, Any]:
    try:
        lock = await _session_lock(session_id)
        async with lock:
            session = _load_session(session_id)
            requirements = session.get("requirement_document")
            architecture = session.get("architecture_document")
            if not isinstance(requirements, dict) or not isinstance(architecture, dict):
                raise WorkflowError(
                    "ARCHITECTURE_NOT_COMPLETED",
                    "必須先完成同一個 session_id 的需求書與架構書。",
                    recoverable=False,
                )
            existing_document = session.get("audit_document")
            existing = session.get("artifacts", {}).get("audit", [])
            if isinstance(existing_document, dict):
                return {
                    "status": "completed", "workflow": "audit",
                    "session_id": session_id, "artifacts": existing,
                    "document": existing_document,
                    "conclusion": existing_document.get("conclusion"),
                    "handoff": existing_document.get("handoff"),
                }
            target = _resolve_output_dir(output_dir, session_id) if output_dir.strip() else Path(session["output_dir"])
            payload, _ = await _sample_validated(
                ctx,
                stage="audit_draft",
                system_prompt=prompts.iso_audit_draft(),
                input_value={
                    "requirement_specification": requirements,
                    "architecture_specification": architecture,
                },
                validator=lambda candidate: _validate_audit_document(
                    candidate, requirements=requirements, session_id=session_id
                ),
            )
            artifacts: list[dict[str, Any]] = []
            if settings.artifacts.enabled:
                target.mkdir(parents=True, exist_ok=True)
                json_path = target / "audit.json"
                _atomic_write_json(json_path, payload)
                md_path = target / "audit.md"
                render_audit(payload, md_path)
                artifacts = [
                    {"kind": "audit_json", "path": str(json_path)},
                    {"kind": "audit_report", "path": str(md_path)},
                ]
            session["audit_document"] = payload
            session.setdefault("artifacts", {})["audit"] = artifacts
            session["phase"] = "audit_completed"
            _save_session(session)
            return {
                "status": "completed", "workflow": "audit",
                "session_id": session_id, "artifacts": artifacts,
                "document": payload, "conclusion": payload.get("conclusion"),
                "handoff": payload.get("handoff"),
            }
    except WorkflowError as error:
        return _error_result("audit", error, session_id)
