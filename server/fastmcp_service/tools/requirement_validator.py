import copy
import json
import re
from pathlib import Path
from typing import Any, Callable


QUESTION_TYPES = {"single_choice", "multi_choice", "yes_no", "fill_in"}
INITIAL_STATUSES = {"pending", "satisfied"}
OPEN_STATUSES = {
    "pending", "answer_received", "partially_answered", "needs_clarification",
    "confirmation_required", "conflict",
}
TERMINAL_STATUSES = {"answered", "answered_by_cross_evidence", "satisfied", "defaulted", "invalidated"}
ASSESSMENT_STATUSES = {"answered", "partially_answered", "needs_clarification", "defaulted", "conflict"}
CROSS_EFFECTS = {"answered_by_cross_evidence", "partially_answered", "confirmation_required", "conflict", "revised"}
CONFIDENCE_LEVELS = {"explicit", "partial", "inferred"}
PROFILE_POLICY_PATH = Path(__file__).resolve().parents[1] / "resources" / "policies" / "profile-policy.json"


def _profile_dimensions(profile: str) -> set[str]:
    try:
        policies = json.loads(PROFILE_POLICY_PATH.read_text(encoding="utf-8"))
        profiles = policies.get("depth_profiles", {})
    except (OSError, json.JSONDecodeError, TypeError):
        return set()
    dimensions: set[str] = set()
    visited: set[str] = set()
    current = profile
    while isinstance(current, str) and current and current not in visited:
        visited.add(current)
        item = profiles.get(current)
        if not isinstance(item, dict):
            break
        dimensions.update(
            str(value) for value in item.get("required", []) if isinstance(value, str)
        )
        current = item.get("inherits")
    return dimensions


def _result(errors: list[str], warnings: list[str], **values: Any) -> dict[str, Any]:
    return {"valid": not errors, "errors": errors, "warnings": warnings, **values}


def _is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _qa_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["id"]: item
        for item in state.get("qa_items", [])
        if isinstance(item, dict) and _is_text(item.get("id"))
    }


def _evidence_is_current(evidence: Any, user_message: str) -> bool:
    if not isinstance(evidence, list) or not evidence:
        return False
    return all(
        _is_text(excerpt) and str(excerpt).strip() in user_message
        for excerpt in evidence
    )


def _validate_question(question: Any, label: str, errors: list[str]) -> None:
    if not isinstance(question, dict):
        errors.append(f"{label} must be an object")
        return
    if question.get("type") not in QUESTION_TYPES:
        errors.append(f"{label}.type is invalid")
    if not _is_text(question.get("text")):
        errors.append(f"{label}.text is required")
    options = question.get("options")
    if not isinstance(options, list):
        errors.append(f"{label}.options must be an array")
        return
    keys: list[str] = []
    for index, option in enumerate(options):
        if not isinstance(option, dict) or not _is_text(option.get("key")) or not _is_text(option.get("label")):
            errors.append(f"{label}.options[{index}] requires key and label")
            continue
        keys.append(str(option["key"]))
    if len(keys) != len(set(keys)):
        errors.append(f"{label}.option keys must be unique")
    if question.get("type") in {"single_choice", "multi_choice"} and len(options) < 2:
        errors.append(f"{label} choice questions require at least two options")


def validate_consultant_plan(payload: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required = {
        "schema_version", "stage", "selected_profile", "topic", "facts", "qa_items",
        "advisory_suggestions", "active_question_id", "converged", "reason",
    }
    missing = sorted(required - payload.keys())
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if payload.get("schema_version") != "2.0":
        errors.append("schema_version must be '2.0'")
    if payload.get("stage") != "consultant_plan":
        errors.append("stage must be 'consultant_plan'")
    if not _is_text(payload.get("selected_profile")):
        errors.append("selected_profile is required")
    topic = payload.get("topic")
    if not isinstance(topic, dict) or not all(_is_text(topic.get(name)) for name in ("raw", "normalized", "language")):
        errors.append("topic requires raw, normalized, and language")
    if not isinstance(payload.get("facts"), dict):
        errors.append("facts must be an object")

    normalized = copy.deepcopy(payload)
    qa_items = normalized.get("qa_items")
    if not isinstance(qa_items, list):
        errors.append("qa_items must be an array")
        qa_items = []
    elif not 3 <= len(qa_items) <= 15:
        errors.append("qa_items must contain 3 to 15 material candidate boundaries")
    ids: list[str] = []
    orders: list[int] = []
    covered_policy_dimensions: set[str] = set()
    required_policy_dimensions = _profile_dimensions(str(payload.get("selected_profile", "")))
    if not required_policy_dimensions:
        errors.append("selected_profile has no authoritative depth policy")
    for index, item in enumerate(qa_items):
        label = f"qa_items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        required_item = {
            "id", "display_order", "dimension", "policy_dimensions", "capability_profile", "target_fact",
            "priority", "status", "question", "answer", "assessment", "follow_ups", "source_turn",
        }
        missing_item = sorted(required_item - item.keys())
        if missing_item:
            errors.append(f"{label} missing: " + ", ".join(missing_item))
        item_id = item.get("id")
        if not _is_text(item_id) or not re.fullmatch(r"Q[1-9][0-9]*", item_id):
            errors.append(f"{label}.id must use Q1..Qn format")
        else:
            ids.append(item_id)
        if not isinstance(item.get("display_order"), int) or item.get("display_order", 0) < 1:
            errors.append(f"{label}.display_order must be a positive integer")
        else:
            orders.append(item["display_order"])
        for name in ("dimension", "capability_profile", "target_fact"):
            if not _is_text(item.get(name)):
                errors.append(f"{label}.{name} is required")
        policy_dimensions = item.get("policy_dimensions")
        if not isinstance(policy_dimensions, list) or not policy_dimensions:
            errors.append(f"{label}.policy_dimensions must be a non-empty array")
            normalized_dimensions: set[str] = set()
        else:
            normalized_dimensions = {
                str(value) for value in policy_dimensions if isinstance(value, str) and value.strip()
            }
            if len(normalized_dimensions) != len(policy_dimensions):
                errors.append(f"{label}.policy_dimensions must contain unique non-empty strings")
            unknown_dimensions = normalized_dimensions - required_policy_dimensions
            if unknown_dimensions:
                errors.append(
                    f"{label}.policy_dimensions contains unauthorized keys: "
                    + ", ".join(sorted(unknown_dimensions))
                )
            covered_policy_dimensions.update(normalized_dimensions & required_policy_dimensions)
        if not isinstance(item.get("priority"), int) or not 1 <= item.get("priority", 0) <= 10:
            errors.append(f"{label}.priority must be 1-10")
        if item.get("status") not in INITIAL_STATUSES:
            errors.append(f"{label}.initial status must be pending or satisfied")
        _validate_question(item.get("question"), f"{label}.question", errors)
        question = item.get("question") if isinstance(item.get("question"), dict) else {}
        if (
            "acceptance_criteria" in normalized_dimensions
            and question.get("type") not in {"multi_choice", "fill_in"}
        ):
            warnings.append(
                f"{label}.question for acceptance_criteria is not multi_choice or fill_in; "
                "PASS because question.type is a View hint and free text remains available"
            )
        if item.get("status") == "pending" and item.get("answer") is not None:
            errors.append(f"{label}.pending answer must be null")
        if item.get("status") == "satisfied" and isinstance(item.get("answer"), str):
            raw_answer = item["answer"]
            item["answer"] = {
                "raw": raw_answer,
                "resolved_values": [raw_answer],
                "normalized": raw_answer,
                "source_turn": 0,
                "source_question_id": item.get("id"),
                "resolution": "seed_explicit",
            }
            warnings.append(f"{label}.answer bare string was normalized to a structured seed answer")
        if item.get("status") == "satisfied" and not isinstance(item.get("answer"), dict):
            errors.append(f"{label}.satisfied item requires a structured answer")
        if item.get("status") == "satisfied" and isinstance(item.get("assessment"), str):
            assessment_text = item["assessment"]
            item["assessment"] = {
                "status": "satisfied",
                "normalized_value": item.get("answer", {}).get("normalized") if isinstance(item.get("answer"), dict) else None,
                "evidence": [item.get("answer", {}).get("raw", "")] if isinstance(item.get("answer"), dict) else [],
                "reason_summary": assessment_text,
            }
            warnings.append(f"{label}.assessment bare string was normalized to a structured assessment")
        if not isinstance(item.get("follow_ups"), list):
            errors.append(f"{label}.follow_ups must be an array")
    if len(ids) != len(set(ids)):
        errors.append("qa item ids must be unique")
    expected_ids = [f"Q{index}" for index in range(1, len(qa_items) + 1)]
    if ids and ids != expected_ids:
        errors.append("qa item ids must be sequential Q1 through Qn in display order")
    if len(orders) != len(set(orders)):
        errors.append("qa item display_order values must be unique")
    missing_policy_dimensions = required_policy_dimensions - covered_policy_dimensions
    if missing_policy_dimensions:
        errors.append(
            "qa_items do not cover required profile dimensions: "
            + ", ".join(sorted(missing_policy_dimensions))
        )
    if not isinstance(payload.get("advisory_suggestions"), list):
        errors.append("advisory_suggestions must be an array")

    by_id = {item.get("id"): item for item in qa_items if isinstance(item, dict)}
    active_id = normalized.get("active_question_id")
    if active_id is not None:
        if active_id not in by_id:
            errors.append("active_question_id must reference an existing QA item")
        elif by_id[active_id].get("status") not in OPEN_STATUSES:
            warnings.append("active_question_id referenced a terminal item and was recalculated")
            active_id = None
    pending = sorted(
        (item for item in qa_items if isinstance(item, dict) and item.get("status") in OPEN_STATUSES),
        key=lambda item: (-item.get("priority", 0), item.get("display_order", 999999)),
    )
    if active_id is None and pending:
        active_id = pending[0].get("id")
    converged = not pending
    if bool(normalized.get("converged")) != converged:
        warnings.append("converged was normalized from QA item statuses")
    normalized["active_question_id"] = None if converged else active_id
    normalized["converged"] = converged

    new_state = {
        "schema_version": "2.0",
        "topic": copy.deepcopy(normalized.get("topic", {})),
        "selected_profile": normalized.get("selected_profile"),
        "facts": copy.deepcopy(normalized.get("facts", {})),
        "qa_items": copy.deepcopy(qa_items),
        "advisory_suggestions": copy.deepcopy(normalized.get("advisory_suggestions", [])),
        "active_question_id": normalized.get("active_question_id"),
        "pending_consultant_review": [],
        "scope_extension_candidates": [],
        "turn_count": 0,
        "converged": normalized.get("converged", False),
        "aborted": False,
    }
    return _result(errors, warnings, normalized_payload=normalized, new_state=new_state)


def validate_consultant_answer_review(
    payload: dict[str, Any], *, user_message: str,
    requirement_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required = {
        "schema_version", "stage", "active_question_id", "capability_profile",
        "focused_assessment", "cross_question_updates", "conflicts", "follow_up",
        "scope_extension_candidates",
    }
    missing = sorted(required - payload.keys())
    if missing:
        errors.append("missing fields: " + ", ".join(missing))
    if payload.get("schema_version") != "2.0":
        errors.append("schema_version must be '2.0'")
    if payload.get("stage") != "consultant_answer_review":
        errors.append("stage must be 'consultant_answer_review'")
    if not _is_text(user_message):
        errors.append("user_message must contain the untouched current user input")

    state = copy.deepcopy(requirement_state or {})
    qa_by_id = _qa_map(state)
    active_id = state.get("active_question_id")
    if payload.get("active_question_id") != active_id or active_id not in qa_by_id:
        errors.append("active_question_id must match the canonical state")
        active_item: dict[str, Any] = {}
    else:
        active_item = qa_by_id[active_id]
    normalized_payload = copy.deepcopy(payload)
    if active_item and payload.get("capability_profile") != active_item.get("capability_profile"):
        warnings.append("capability_profile display name was normalized to the canonical active-question id")
        normalized_payload["capability_profile"] = active_item.get("capability_profile")
    assessment = payload.get("focused_assessment")
    if not isinstance(assessment, dict):
        errors.append("focused_assessment must be an object")
        assessment = {}
    if assessment.get("status") not in ASSESSMENT_STATUSES:
        errors.append("focused_assessment.status is invalid")
    for name in ("normalized_value", "evidence", "reason_summary"):
        if name not in assessment:
            errors.append(f"focused_assessment.{name} is required")
    if not isinstance(assessment.get("evidence"), list):
        errors.append("focused_assessment.evidence must be an array")
    elif active_item and assessment.get("status") != "needs_clarification" and not _evidence_is_current(assessment.get("evidence"), user_message):
        errors.append("focused_assessment.evidence must quote the current user_message")

    cross_updates = payload.get("cross_question_updates")
    if not isinstance(cross_updates, list):
        errors.append("cross_question_updates must be an array")
        cross_updates = []
    accepted_cross: list[dict[str, Any]] = []
    for index, update in enumerate(cross_updates):
        label = f"cross_question_updates[{index}]"
        if not isinstance(update, dict):
            warnings.append(f"{label} was ignored because it is not an object")
            continue
        question_id = update.get("question_id")
        effect = update.get("effect")
        confidence = update.get("confidence")
        evidence = update.get("evidence")
        if question_id not in qa_by_id or question_id == active_id:
            warnings.append(f"{label} was ignored because it does not reference another existing question")
            continue
        if effect not in CROSS_EFFECTS or confidence not in CONFIDENCE_LEVELS:
            warnings.append(f"{label} was ignored because effect or confidence is invalid")
            continue
        if not _evidence_is_current(evidence, user_message):
            warnings.append(f"{label} was ignored because evidence does not quote the current user_message")
            continue
        if effect == "answered_by_cross_evidence" and confidence != "explicit":
            warnings.append(f"{label} was downgraded to confirmation_required because it was not explicit")
            update = copy.deepcopy(update)
            update["effect"] = "confirmation_required"
        accepted_cross.append(copy.deepcopy(update))

    conflicts = payload.get("conflicts")
    if not isinstance(conflicts, list):
        errors.append("conflicts must be an array")
        conflicts = []
    extension_candidates = payload.get("scope_extension_candidates")
    if not isinstance(extension_candidates, list):
        errors.append("scope_extension_candidates must be an array")
        extension_candidates = []
    accepted_extensions: list[dict[str, Any]] = []
    for index, candidate in enumerate(extension_candidates):
        label = f"scope_extension_candidates[{index}]"
        if not isinstance(candidate, dict):
            warnings.append(f"{label} was ignored because it is not an object")
            continue
        if not all(_is_text(candidate.get(name)) for name in ("title", "description", "reason")):
            warnings.append(f"{label} was ignored because title, description, or reason is missing")
            continue
        if not _evidence_is_current(candidate.get("evidence"), user_message):
            warnings.append(f"{label} was ignored because evidence does not quote the current user_message")
            continue
        accepted_extensions.append(copy.deepcopy(candidate))
    follow_up = payload.get("follow_up")
    if follow_up is not None:
        _validate_question(follow_up, "follow_up", errors)
        if isinstance(follow_up, dict) and follow_up.get("question_id") != active_id:
            errors.append("follow_up must belong to the active question")
    if assessment.get("status") == "needs_clarification" and follow_up is None:
        errors.append("needs_clarification requires one follow_up")

    if errors:
        return _result(errors, warnings, normalized_payload=normalized_payload)

    previous = active_item.get("answer")
    history = list(previous.get("history") or []) if isinstance(previous, dict) else []
    if isinstance(previous, dict):
        history.append(copy.deepcopy(previous))
    active_item["answer"] = {
        "raw": user_message,
        "resolved_values": [assessment.get("normalized_value")]
        if assessment.get("normalized_value") is not None else [],
        "input_resolution": "llm_review",
        "source_turn": int(state.get("turn_count", 0)) + 1,
        "source_question_id": active_id,
        "history": history,
    }
    active_item["assessment"] = copy.deepcopy(assessment)
    active_status = assessment["status"]
    active_item["status"] = active_status
    if isinstance(active_item.get("answer"), dict):
        active_item["answer"]["normalized"] = assessment.get("normalized_value")
        active_item["answer"]["resolution"] = active_status
    if follow_up is not None:
        active_item.setdefault("follow_ups", []).append(copy.deepcopy(follow_up))

    current_raw = user_message
    turn_count = int(state.get("turn_count", 0))
    for update in accepted_cross:
        target = qa_by_id[update["question_id"]]
        effect = update["effect"]
        if effect in {"conflict", "revised"} and target.get("status") in TERMINAL_STATUSES:
            target.setdefault("conflict_history", []).append(copy.deepcopy(update))
            target["status"] = "conflict" if effect == "conflict" else "confirmation_required"
            continue
        if target.get("status") in TERMINAL_STATUSES:
            warnings.append(f"{target['id']} was already terminal; non-conflict cross update was ignored")
            continue
        target["status"] = "confirmation_required" if effect == "revised" else effect
        target["assessment"] = {
            "status": effect,
            "normalized_value": update.get("normalized_value"),
            "evidence": copy.deepcopy(update.get("evidence", [])),
            "confidence": update.get("confidence"),
            "source_question_id": active_id,
        }
        target["answer"] = {
            "raw": current_raw,
            "normalized": update.get("normalized_value"),
            "source_turn": turn_count + 1,
            "source_question_id": active_id,
            "resolution": effect,
        }

    state.setdefault("pending_consultant_review", []).extend(copy.deepcopy(conflicts))
    legacy_extensions = state.pop("new_question_proposals", [])
    stored_extensions = state.setdefault("scope_extension_candidates", [])
    stored_extensions.extend(copy.deepcopy(legacy_extensions))
    known_extensions = {
        (
            str(item.get("title", "")).strip().casefold(),
            str(item.get("description", "")).strip().casefold(),
        )
        for item in stored_extensions
        if isinstance(item, dict)
    }
    for candidate in accepted_extensions:
        identity = (
            str(candidate.get("title", "")).strip().casefold(),
            str(candidate.get("description", "")).strip().casefold(),
        )
        if identity in known_extensions:
            warnings.append(f"duplicate scope extension '{candidate.get('title')}' was ignored")
            continue
        stored_extensions.append(candidate)
        known_extensions.add(identity)
    state["turn_count"] = turn_count + 1

    if active_item.get("status") in {"needs_clarification", "partially_answered", "conflict"}:
        next_id = active_id
    else:
        open_items = sorted(
            (item for item in state.get("qa_items", []) if item.get("status") in OPEN_STATUSES),
            key=lambda item: (-item.get("priority", 0), item.get("display_order", 999999)),
        )
        next_id = open_items[0]["id"] if open_items else None
    state["active_question_id"] = next_id
    state["converged"] = next_id is None
    return _result(
        [], warnings, normalized_payload=normalized_payload, new_state=state,
        applied_cross_question_updates=accepted_cross, converged=state["converged"],
    )


def validate_consultant_plan_review(
    reviewed: dict[str, Any], *, draft_plan: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate a release-gated plan and prevent the reviewer from expanding Q0."""
    validation = validate_consultant_plan(reviewed)
    errors = list(validation.get("errors", []))
    warnings = list(validation.get("warnings", []))
    draft = draft_plan or {}

    draft_topic = draft.get("topic") if isinstance(draft.get("topic"), dict) else {}
    reviewed_topic = reviewed.get("topic") if isinstance(reviewed.get("topic"), dict) else {}
    if draft_topic.get("raw") != reviewed_topic.get("raw"):
        errors.append("reviewed topic.raw must exactly preserve the draft Q0")
    if draft.get("selected_profile") != reviewed.get("selected_profile"):
        errors.append("reviewed selected_profile must exactly preserve the authorized profile")

    draft_ids = {
        item.get("id") for item in draft.get("qa_items", [])
        if isinstance(item, dict) and _is_text(item.get("id"))
    }
    reviewed_ids = {
        item.get("id") for item in reviewed.get("qa_items", [])
        if isinstance(item, dict) and _is_text(item.get("id"))
    }
    if reviewed_ids != draft_ids:
        errors.append("review must preserve the complete draft Q1..Qn id set")

    validation["valid"] = not errors
    validation["errors"] = errors
    validation["warnings"] = warnings
    return validation


def validate_specialist_turn(
    payload: dict[str, Any], *, requirement_state: dict[str, Any] | None = None,
    assigned_boundary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    del assigned_boundary
    state = requirement_state or {}
    active = _qa_map(state).get(state.get("active_question_id"), {})
    answer = active.get("answer") if isinstance(active.get("answer"), dict) else {}
    return validate_consultant_answer_review(
        payload,
        user_message=str(answer.get("raw", "")),
        requirement_state=state,
    )


def validate_consultant_reconciliation(
    payload: dict[str, Any], *, requirement_state: dict[str, Any] | None = None
) -> dict[str, Any]:
    del payload
    return _result(
        ["consultant_reconciliation is maintenance-only in State 2.0; use consultant_answer_review"],
        [], new_state=copy.deepcopy(requirement_state or {}),
    )


def validate_interview_step(
    payload: dict[str, Any], *, requirement_state: dict[str, Any] | None = None,
    answered_question: dict[str, Any] | None = None, normalized_latest_answer: str = "",
    answer_resolution: str = "free_text",
) -> dict[str, Any]:
    del answered_question, answer_resolution
    if payload.get("stage") == "consultant_plan":
        return validate_consultant_plan(payload)
    if payload.get("stage") == "consultant_answer_review":
        return validate_consultant_answer_review(
            payload,
            user_message=normalized_latest_answer,
            requirement_state=requirement_state,
        )
    return _result(["unsupported requirement interview stage"], [])


def _optional_json_object(value: str) -> dict[str, Any]:
    if not value:
        return {}
    parsed = json.loads(value)
    return parsed if isinstance(parsed, dict) else {}


def _validate_json(payload_json: str, validator: Callable[[dict[str, Any]], dict[str, Any]]) -> str:
    try:
        payload = json.loads(payload_json)
    except json.JSONDecodeError as error:
        return json.dumps(_result([f"invalid JSON: {error.msg}"], []), ensure_ascii=False)
    if not isinstance(payload, dict):
        return json.dumps(_result(["payload must be an object"], []), ensure_ascii=False)
    return json.dumps(validator(payload), ensure_ascii=False)


def validate_consultant_plan_json(payload_json: str) -> str:
    return _validate_json(payload_json, validate_consultant_plan)


def validate_consultant_plan_review_json(
    payload_json: str, *, draft_plan_json: str = ""
) -> str:
    try:
        draft = _optional_json_object(draft_plan_json)
    except json.JSONDecodeError as error:
        return json.dumps(_result([f"invalid draft_plan JSON: {error.msg}"], []), ensure_ascii=False)
    return _validate_json(
        payload_json,
        lambda payload: validate_consultant_plan_review(payload, draft_plan=draft),
    )


def validate_consultant_answer_review_json(
    payload_json: str, *, user_message: str, requirement_state_json: str = ""
) -> str:
    try:
        state = _optional_json_object(requirement_state_json)
    except json.JSONDecodeError as error:
        return json.dumps(_result([f"invalid requirement_state JSON: {error.msg}"], []), ensure_ascii=False)
    return _validate_json(
        payload_json,
        lambda payload: validate_consultant_answer_review(
            payload, user_message=user_message, requirement_state=state
        ),
    )


def validate_specialist_turn_json(
    payload_json: str, *, requirement_state_json: str = "", assigned_boundary_json: str = ""
) -> str:
    del assigned_boundary_json
    state = _optional_json_object(requirement_state_json)
    active = next(
        (
            item for item in state.get("qa_items", [])
            if isinstance(item, dict) and item.get("id") == state.get("active_question_id")
        ),
        {},
    )
    answer = active.get("answer") if isinstance(active.get("answer"), dict) else {}
    return validate_consultant_answer_review_json(
        payload_json,
        user_message=str(answer.get("raw", "")),
        requirement_state_json=requirement_state_json,
    )


def validate_consultant_reconciliation_json(
    payload_json: str, *, requirement_state_json: str = ""
) -> str:
    try:
        state = _optional_json_object(requirement_state_json)
    except json.JSONDecodeError as error:
        return json.dumps(_result([f"invalid requirement_state JSON: {error.msg}"], []), ensure_ascii=False)
    return _validate_json(payload_json, lambda payload: validate_consultant_reconciliation(payload, requirement_state=state))


def validate_interview_step_json(
    payload_json: str, *, requirement_state_json: str = "", answered_question_json: str = "",
    normalized_latest_answer: str = "", answer_resolution: str = "free_text",
) -> str:
    del answered_question_json, normalized_latest_answer, answer_resolution
    try:
        state = _optional_json_object(requirement_state_json)
    except json.JSONDecodeError as error:
        return json.dumps(_result([f"invalid validation context JSON: {error.msg}"], []), ensure_ascii=False)
    return _validate_json(payload_json, lambda payload: validate_interview_step(payload, requirement_state=state))
