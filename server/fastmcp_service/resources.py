import json
from .mcp_instance import mcp
from pathlib import Path

ROOT = Path(__file__).parent


def _read_resource(relative_path: str) -> str:
    """Read a UTF-8 resource bundled with the LogicMCP server."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


@mcp.resource("config://logicmcp")
def get_logicmcp_config() -> str:
    return json.dumps({
        "server_name": "LogicMCP Federated Server",
        "version": "2.0.0-experimental",
        "supported_depth_profiles": ["simple", "professional", "consultant"],
        "question_count_policy": "dynamic",
        "requirement_flow": ["consultant_plan", "consultant_answer_review"],
        "workflow_owner": "python_factory",
        "membership_aware": False,
    }, ensure_ascii=False)

@mcp.resource("policy://profiles")
def get_profile_policy() -> str:
    return _read_resource("resources/policies/profile-policy.json")

@mcp.resource("policy://domain")
def get_domain_policy() -> str:
    return _read_resource("resources/policies/domain-policy.json")

@mcp.resource("schema://software-specification")
def get_specification_schema() -> str:
    return _read_resource("resources/schemas/specification-schema.json")

@mcp.resource("schema://requirement-state")
def get_requirement_state_schema() -> str:
    return _read_resource("resources/schemas/requirement-state.schema.json")

@mcp.resource("schema://requirement-interview-step")
def get_requirement_interview_step_schema() -> str:
    return _read_resource("resources/schemas/interview-step.schema.json")


@mcp.resource("schema://consultant-plan")
def get_consultant_plan_schema() -> str:
    return _read_resource("resources/schemas/consultant-plan.schema.json")


@mcp.resource("schema://specialist-turn")
def get_specialist_turn_schema() -> str:
    return _read_resource("resources/schemas/specialist-turn.schema.json")


@mcp.resource("schema://consultant-answer-review")
def get_consultant_answer_review_schema() -> str:
    return _read_resource("resources/schemas/consultant-answer-review.schema.json")


@mcp.resource("schema://consultant-reconciliation")
def get_consultant_reconciliation_schema() -> str:
    return _read_resource("resources/schemas/consultant-reconciliation.schema.json")

@mcp.resource("schema://technical-alignment-draft")
def get_technical_alignment_draft_schema() -> str:
    return _read_resource("resources/schemas/technical-alignment-draft.schema.json")

@mcp.resource("schema://audit-draft")
def get_audit_draft_schema() -> str:
    return _read_resource("resources/schemas/audit-draft.schema.json")
