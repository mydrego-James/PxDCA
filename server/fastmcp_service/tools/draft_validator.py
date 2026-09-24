import json
from typing import Any


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _validate_common(
    payload: dict[str, Any], required: set[str], stage: str, schema_version: str = "1.0"
) -> list[str]:
    errors: list[str] = []
    missing = sorted(required - payload.keys())
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if payload.get("schema_version") != schema_version:
        errors.append(f"schema_version must be '{schema_version}'")
    if payload.get("stage") != stage:
        errors.append(f"stage must be '{stage}'")
    if payload.get("status") != "draft":
        errors.append("status must be 'draft'")
    return errors


def validate_technical_alignment_draft(payload: dict[str, Any]) -> dict[str, Any]:
    errors = _validate_common(
        payload,
        {
            "schema_version", "stage", "status", "source_requirement_session_id", "project",
            "requirement_alignment", "architecture_outline", "technical_choices", "assumptions",
            "unresolved_decisions", "limitations",
        },
        "technical_alignment_draft",
    )
    project = payload.get("project")
    if not isinstance(project, dict) or not _has_text(project.get("name")) or not _has_text(project.get("purpose")):
        errors.append("project requires name and purpose")
    alignment = payload.get("requirement_alignment")
    if not isinstance(alignment, list) or not alignment:
        errors.append("requirement_alignment must be a non-empty array")
    else:
        for index, item in enumerate(alignment):
            if not isinstance(item, dict) or not _has_text(item.get("requirement_id")) or not _has_text(item.get("summary")):
                errors.append(f"requirement_alignment[{index}] requires requirement_id and summary")
                continue
            if not isinstance(item.get("technical_implications"), list):
                errors.append(f"requirement_alignment[{index}].technical_implications must be an array")
            architecture_acceptance = item.get("architecture_acceptance_criteria")
            if (
                not isinstance(architecture_acceptance, list)
                or not architecture_acceptance
                or not all(_has_text(value) for value in architecture_acceptance)
            ):
                errors.append(
                    f"requirement_alignment[{index}].architecture_acceptance_criteria "
                    "must be a non-empty text array"
                )
            if item.get("coverage_status") not in {"covered", "partial", "unresolved"}:
                errors.append(f"requirement_alignment[{index}] has invalid coverage_status")
    if not isinstance(payload.get("architecture_outline"), list):
        errors.append("architecture_outline must be an array")
    if not isinstance(payload.get("technical_choices"), list):
        errors.append("technical_choices must be an array")
    for name in ("assumptions", "unresolved_decisions", "limitations"):
        if payload.get(name) is None:
            payload[name] = []
        if not isinstance(payload[name], list):
            errors.append(f"{name} must be an array")
    for index, item in enumerate(payload.get("unresolved_decisions") or []):
        if not isinstance(item, dict) or not _has_text(item.get("id")) or not _has_text(item.get("description")):
            errors.append(f"unresolved_decisions[{index}] requires id and description")
        elif not isinstance(item.get("blocking"), bool):
            errors.append(f"unresolved_decisions[{index}].blocking must be boolean")
    return {"valid": not errors, "errors": errors}


def validate_batch_audit_draft(payload: dict[str, Any]) -> dict[str, Any]:
    errors = _validate_common(
        payload,
        {
            "schema_version", "stage", "status", "source_requirement_session_id", "project_name",
            "project", "scope", "core_requirements", "add_on_services", "unresolved_items",
        },
        "batch_audit_draft",
    )
    if not _has_text(payload.get("source_requirement_session_id")):
        errors.append("source_requirement_session_id is required")

    project = payload.get("project")
    if not isinstance(project, dict):
        errors.append("project must be an object")
    else:
        for name in ("name", "topic", "summary", "objective"):
            if not _has_text(project.get(name)):
                errors.append(f"project.{name} is required")
        if not isinstance(project.get("target_users"), list):
            errors.append("project.target_users must be an array")

    scope = payload.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        for name in ("in_scope", "out_of_scope"):
            if not isinstance(scope.get(name), list):
                errors.append(f"scope.{name} must be an array")

    core = payload.get("core_requirements")
    if not isinstance(core, list) or not core:
        errors.append("core_requirements must be a non-empty array")
    else:
        for index, item in enumerate(core):
            if not isinstance(item, dict):
                errors.append(f"core_requirements[{index}] must be an object")
                continue
            for name in ("id", "title", "category", "description", "rationale", "source_boundary"):
                if not _has_text(item.get(name)):
                    errors.append(f"core_requirements[{index}].{name} is required")
            if item.get("category") not in {
                "business", "functional", "data", "integration", "security",
                "non_functional", "deployment",
            }:
                errors.append(f"core_requirements[{index}].category is invalid")

    addon = payload.get("add_on_services")
    if not isinstance(addon, list):
        errors.append("add_on_services must be an array")
    else:
        for index, item in enumerate(addon):
            if (
                not isinstance(item, dict)
                or not _has_text(item.get("id"))
                or not _has_text(item.get("title"))
                or not _has_text(item.get("description"))
                or not _has_text(item.get("reason"))
            ):
                errors.append(f"add_on_services[{index}] requires id, title, description, and reason")

    if not isinstance(payload.get("unresolved_items"), list):
        errors.append("unresolved_items must be an array")

    return {"valid": not errors, "errors": errors}


def validate_audit_draft(payload: dict[str, Any]) -> dict[str, Any]:
    errors = _validate_common(
        payload,
        {
            "schema_version", "stage", "status", "source_requirement_session_id", "project_name",
            "audit_basis", "coverage", "findings", "blockers", "conclusion", "handoff",
            "limitations",
        },
        "audit_draft",
        "1.1",
    )
    if not isinstance(payload.get("audit_basis"), list):
        errors.append("audit_basis must be an array")
    coverage = payload.get("coverage")
    if not isinstance(coverage, list):
        errors.append("coverage must be an array")
    else:
        for index, item in enumerate(coverage):
            if not isinstance(item, dict) or not _has_text(item.get("requirement_id")):
                errors.append(f"coverage[{index}] requires requirement_id")
                continue
            if item.get("status") not in {"covered", "partial", "missing", "conflict", "requires_confirmation"}:
                errors.append(f"coverage[{index}] has invalid status")
            if not isinstance(item.get("evidence"), list):
                errors.append(f"coverage[{index}].evidence must be an array")
            if not isinstance(item.get("gap"), str):
                errors.append(f"coverage[{index}].gap must be a string")
    findings = payload.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array")
    else:
        for index, item in enumerate(findings):
            if not isinstance(item, dict) or not _has_text(item.get("finding_id")) or not _has_text(item.get("description")):
                errors.append(f"findings[{index}] requires finding_id and description")
                continue
            if item.get("type") not in {"coverage", "conflict", "assumption", "scope", "traceability", "other"}:
                errors.append(f"findings[{index}] has invalid type")
            if item.get("severity") not in {"blocker", "major", "minor", "observation"}:
                errors.append(f"findings[{index}] has invalid severity")
            if not isinstance(item.get("recommendation"), str):
                errors.append(f"findings[{index}].recommendation must be a string")
            if not isinstance(item.get("requirement_ids"), list):
                errors.append(f"findings[{index}].requirement_ids must be an array")
    if not isinstance(payload.get("blockers"), list):
        errors.append("blockers must be an array")
    if payload.get("conclusion") not in {"draft_pending_review", "draft_blocked", "draft_ready_for_review"}:
        errors.append("invalid conclusion")
    handoff = payload.get("handoff")
    if not isinstance(handoff, dict):
        errors.append("handoff must be an object")
    else:
        if handoff.get("disposition") not in {
            "ready_for_handoff", "revise_pm", "revise_pg", "user_decision_required", "hold",
        }:
            errors.append("handoff has invalid disposition")
        if handoff.get("recommended_owner") not in {
            "requester", "pm", "pg", "executor", "external",
        }:
            errors.append("handoff has invalid recommended_owner")
        if not _has_text(handoff.get("next_purpose")):
            errors.append("handoff.next_purpose is required")
        for name in ("required_actions", "evidence_refs", "unresolved_risks"):
            values = handoff.get(name)
            if not isinstance(values, list) or not all(_has_text(value) for value in values):
                errors.append(f"handoff.{name} must be a text array")
        if handoff.get("disposition") == "ready_for_handoff" and payload.get("blockers"):
            errors.append("ready_for_handoff is invalid when blockers exist")
    if not isinstance(payload.get("limitations"), list):
        errors.append("limitations must be an array")
    return {"valid": not errors, "errors": errors}


def _validate_json(payload_json: str, validator) -> str:
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as error:
        return json.dumps({"valid": False, "errors": [f"invalid JSON: {error.msg}"]}, ensure_ascii=False)
    if not isinstance(payload, dict):
        return json.dumps({"valid": False, "errors": ["payload must be an object"]}, ensure_ascii=False)
    return json.dumps(validator(payload), ensure_ascii=False)


def validate_batch_audit_draft_json(payload_json: str) -> str:
    return _validate_json(payload_json, validate_batch_audit_draft)


def validate_technical_alignment_draft_json(payload_json: str) -> str:
    return _validate_json(payload_json, validate_technical_alignment_draft)


def validate_audit_draft_json(payload_json: str) -> str:
    return _validate_json(payload_json, validate_audit_draft)
