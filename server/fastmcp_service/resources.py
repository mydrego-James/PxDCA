import json
from pathlib import Path

ROOT = Path(__file__).parent


def _read_resource(relative_path: str) -> str:
    """Read a UTF-8 resource bundled with the LogicMCP server."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


def get_logicmcp_config() -> str:
    return json.dumps({
        "server_name": "LogicMCP Federated Server",
        "version": "3.0.0",
        "supported_depth_profiles": ["simple", "professional", "consultant"],
        "question_count_policy": "dynamic",
        "requirement_flow": ["consultant_plan", "consultant_answer_review"],
        "workflow_owner": "logicmcp_server",
        "membership_aware": False,
    }, ensure_ascii=False)

def get_profile_policy() -> str:
    return _read_resource("resources/policies/profile-policy.json")

def get_domain_policy() -> str:
    return _read_resource("resources/policies/domain-policy.json")

def get_specification_schema() -> str:
    return _read_resource("resources/schemas/specification-schema.json")

def get_requirement_state_schema() -> str:
    return _read_resource("resources/schemas/requirement-state.schema.json")

def get_requirement_interview_step_schema() -> str:
    return _read_resource("resources/schemas/interview-step.schema.json")


def get_consultant_plan_schema() -> str:
    return _read_resource("resources/schemas/consultant-plan.schema.json")


def get_specialist_turn_schema() -> str:
    return _read_resource("resources/schemas/specialist-turn.schema.json")


def get_consultant_answer_review_schema() -> str:
    return _read_resource("resources/schemas/consultant-answer-review.schema.json")


def get_consultant_reconciliation_schema() -> str:
    return _read_resource("resources/schemas/consultant-reconciliation.schema.json")

def get_technical_alignment_draft_schema() -> str:
    return _read_resource("resources/schemas/technical-alignment-draft.schema.json")

def get_audit_draft_schema() -> str:
    return _read_resource("resources/schemas/audit-draft.schema.json")
