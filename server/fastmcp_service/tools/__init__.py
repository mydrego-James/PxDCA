import hashlib
import json
from pathlib import Path

from .audit_renderer import render_audit
from .baseline_renderer import render_enterprise_delivery, render_requirement_spec, render_planning_spec
from .specification_renderer import render_specification
from .requirement_validator import (
    validate_consultant_answer_review_json,
    validate_consultant_plan_json,
    validate_consultant_plan_review_json,
    validate_consultant_reconciliation_json,
    validate_interview_step_json,
    validate_specialist_turn_json,
)
from .draft_validator import (
    validate_audit_draft_json,
    validate_technical_alignment_draft_json,
    validate_batch_audit_draft_json,
)
from ..mcp_instance import mcp, OUTPUT_ROOT, logger


def _output_path(value: str) -> Path:
    """Resolve client output while giving relative paths an MCP-owned root."""
    requested = Path(value)
    if requested.is_absolute():
        return requested.resolve()

    resolved = (OUTPUT_ROOT / requested).resolve()
    if resolved != OUTPUT_ROOT and OUTPUT_ROOT not in resolved.parents:
        raise ValueError("Relative output path must remain inside MCP_OUTPUT_ROOT")
    return resolved

def _output_dir(output_dir: str) -> Path:
    path = _output_path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _log_validation(
    tool_name: str,
    *,
    trace_id: str,
    payload_json: str,
    result_json: str,
) -> None:
    """Log deterministic validation evidence without duplicating user content."""
    payload_digest = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()[:16]
    payload_stage = "unknown"
    payload_items = None
    try:
        payload = json.loads(payload_json)
        if isinstance(payload, dict):
            payload_stage = str(payload.get("stage", "unknown"))
            items = payload.get("qa_items")
            payload_items = len(items) if isinstance(items, list) else None
    except json.JSONDecodeError:
        payload_stage = "invalid_json"

    logger.info(
        f"[VALIDATION REQUEST] trace_id={trace_id or 'untracked'} tool={tool_name} "
        f"stage={payload_stage} bytes={len(payload_json.encode('utf-8'))} "
        f"sha256={payload_digest} qa_items={payload_items}"
    )
    try:
        result = json.loads(result_json)
        logger.info(
            f"[VALIDATION RESULT] trace_id={trace_id or 'untracked'} tool={tool_name} "
            f"valid={result.get('valid')} errors={json.dumps(result.get('errors', []), ensure_ascii=False)} "
            f"warnings={json.dumps(result.get('warnings', []), ensure_ascii=False)}"
        )
    except json.JSONDecodeError:
        logger.error(
            f"[VALIDATION RESULT] trace_id={trace_id or 'untracked'} tool={tool_name} "
            "returned invalid JSON"
        )

@mcp.tool()
def render_software_specification(output_dir: str, payload_json: str) -> str:
    """Render an already validated specification payload without owning APP session state.
    (See schema://software-specification for the payload JSON schema.)
    """
    logger.info(f"Tool called: render_software_specification with output_dir={output_dir}")
    payload = json.loads(payload_json)
    outputs = render_specification(payload, _output_dir(output_dir))
    logger.info("Tool finished: render_software_specification")
    return json.dumps({"outputs": outputs}, ensure_ascii=False)

@mcp.tool()
def render_iso_aligned_audit(output_dir: str, payload_json: str) -> str:
    logger.info(f"[TOOL] render_iso_aligned_audit called with output_dir={output_dir}")
    target = _output_dir(output_dir) / "audit.md"
    result = json.dumps({"output": render_audit(json.loads(payload_json), target)}, ensure_ascii=False)
    logger.info(f"[TOOL] render_iso_aligned_audit finished")
    return result

@mcp.tool()
def render_enterprise_baseline(output_dir: str, payload_json: str) -> str:
    logger.info(f"[TOOL] render_enterprise_baseline called with output_dir={output_dir}")
    target = _output_dir(output_dir) / "enterprise-delivery-baseline.md"
    result = json.dumps(render_enterprise_delivery(json.loads(payload_json), target), ensure_ascii=False)
    logger.info(f"[TOOL] render_enterprise_baseline finished")
    return result

@mcp.tool()
def render_requirement_baseline(output_dir: str, payload_json: str) -> str:
    logger.info(f"[TOOL] render_requirement_baseline called with output_dir={output_dir}")
    target = _output_dir(output_dir) / "requirement-spec.md"
    result = json.dumps(render_requirement_spec(json.loads(payload_json), target), ensure_ascii=False)
    logger.info(f"[TOOL] render_requirement_baseline finished")
    return result

@mcp.tool()
def render_planning_baseline(output_dir: str, payload_json: str) -> str:
    logger.info(f"[TOOL] render_planning_baseline called with output_dir={output_dir}")
    target = _output_dir(output_dir) / "planning-spec.md"
    result = json.dumps(render_planning_spec(json.loads(payload_json), target), ensure_ascii=False)
    logger.info(f"[TOOL] render_planning_baseline finished")
    return result

@mcp.tool()
def validate_requirement_interview_step(
    payload_json: str,
    requirement_state_json: str = "",
    answered_question_json: str = "",
    normalized_latest_answer: str = "",
    answer_resolution: str = "free_text",
) -> str:
    """Validate one Agent-produced requirement interview step deterministically."""
    logger.info(f"[TOOL] validate_requirement_interview_step called")
    res = validate_interview_step_json(
        payload_json,
        requirement_state_json=requirement_state_json,
        answered_question_json=answered_question_json,
        normalized_latest_answer=normalized_latest_answer,
        answer_resolution=answer_resolution,
    )
    logger.info(f"[TOOL] validate_requirement_interview_step finished")
    return res


@mcp.tool()
def validate_consultant_plan(payload_json: str, trace_id: str = "") -> str:
    """Validate the consultant's initial dynamic boundary map and routing decision."""
    logger.info("[TOOL] validate_consultant_plan called")
    res = validate_consultant_plan_json(payload_json)
    _log_validation(
        "validate_consultant_plan",
        trace_id=trace_id,
        payload_json=payload_json,
        result_json=res,
    )
    logger.info("[TOOL] validate_consultant_plan finished")
    return res


@mcp.tool()
def validate_specialist_turn(
    payload_json: str,
    requirement_state_json: str = "",
    assigned_boundary_json: str = "",
) -> str:
    """Validate one specialist result without allowing cross-domain state updates."""
    logger.info("[TOOL] validate_specialist_turn called")
    res = validate_specialist_turn_json(
        payload_json,
        requirement_state_json=requirement_state_json,
        assigned_boundary_json=assigned_boundary_json,
    )
    logger.info("[TOOL] validate_specialist_turn finished")
    return res


@mcp.tool()
def validate_consultant_plan_review(
    payload_json: str,
    draft_plan_json: str = "",
    trace_id: str = "",
) -> str:
    """Validate the background-reviewed plan and reject Q0 or registry expansion."""
    logger.info("[TOOL] validate_consultant_plan_review called")
    res = validate_consultant_plan_review_json(
        payload_json,
        draft_plan_json=draft_plan_json,
    )
    _log_validation(
        "validate_consultant_plan_review",
        trace_id=trace_id,
        payload_json=payload_json,
        result_json=res,
    )
    logger.info("[TOOL] validate_consultant_plan_review finished")
    return res


@mcp.tool()
def validate_consultant_answer_review(
    payload_json: str,
    user_message: str,
    requirement_state_json: str = "",
    trace_id: str = "",
) -> str:
    """Validate and apply one State 2.0 answer-review patch deterministically."""
    logger.info("[TOOL] validate_consultant_answer_review called")
    res = validate_consultant_answer_review_json(
        payload_json,
        user_message=user_message,
        requirement_state_json=requirement_state_json,
    )
    _log_validation(
        "validate_consultant_answer_review",
        trace_id=trace_id,
        payload_json=payload_json,
        result_json=res,
    )
    logger.info("[TOOL] validate_consultant_answer_review finished")
    return res


@mcp.tool()
def validate_consultant_reconciliation(
    payload_json: str,
    requirement_state_json: str = "",
) -> str:
    """Validate and apply the consultant's cross-domain state transition and next route."""
    logger.info("[TOOL] validate_consultant_reconciliation called")
    res = validate_consultant_reconciliation_json(
        payload_json,
        requirement_state_json=requirement_state_json,
    )
    logger.info("[TOOL] validate_consultant_reconciliation finished")
    return res

@mcp.tool()
def validate_technical_alignment_draft(payload_json: str, trace_id: str = "") -> str:
    """Validate one technical alignment draft before APP stores it.
    (See schema://technical-alignment-draft for payload structure.)
    """
    logger.info("Tool called: validate_technical_alignment_draft")
    res = validate_technical_alignment_draft_json(payload_json)
    _log_validation(
        "validate_technical_alignment_draft",
        trace_id=trace_id,
        payload_json=payload_json,
        result_json=res,
    )
    logger.info("Tool finished: validate_technical_alignment_draft")
    return res

@mcp.tool()
def validate_batch_audit_draft(payload_json: str, trace_id: str = "") -> str:
    """Validate a batch audit draft before APP stores it."""
    logger.info("Tool called: validate_batch_audit_draft")
    res = validate_batch_audit_draft_json(payload_json)
    _log_validation(
        "validate_batch_audit_draft",
        trace_id=trace_id,
        payload_json=payload_json,
        result_json=res,
    )
    logger.info("Tool finished: validate_batch_audit_draft")
    return res

@mcp.tool()
def validate_audit_draft(payload_json: str, trace_id: str = "") -> str:
    logger.info(f"[TOOL] validate_audit_draft called")
    res = validate_audit_draft_json(payload_json)
    _log_validation(
        "validate_audit_draft",
        trace_id=trace_id,
        payload_json=payload_json,
        result_json=res,
    )
    logger.info(f"[TOOL] validate_audit_draft finished")
    return res

@mcp.tool()
def save_converged_requirements(output_path: str, payload_json: str) -> str:
    """Save the final, clean converged requirement list as a JSON file.
    Call this tool when the requirement interview is complete and converged.
    """
    logger.info(f"[TOOL] save_converged_requirements called for output_path={output_path}")
    target = _output_path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload_json, encoding="utf-8")
    result = json.dumps({"status": "success", "file": str(target)}, ensure_ascii=False)
    logger.info(f"[TOOL] save_converged_requirements finished")
    return result

@mcp.tool()
def get_available_templates() -> str:
    """Get capability-focus templates available to the single Lead Requirement Consultant."""
    logger.info("Tool called: get_available_templates")
    template_path = Path(__file__).parent.parent / "resources" / "templates" / "profiles.json"
    if not template_path.exists():
        logger.warning("profiles.json not found")
        return "{}"
    profiles = json.loads(template_path.read_text(encoding="utf-8"))
    for capability_id, item in profiles.items():
        if isinstance(item, dict):
            item["capability_id"] = capability_id
            item["kind"] = "capability_focus"
    result = json.dumps(profiles, ensure_ascii=False)
    logger.info("Tool finished: get_available_templates")
    return result
