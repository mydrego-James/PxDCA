from .mcp_instance import logger
from pathlib import Path
import json

ROOT = Path(__file__).parent


def _read_prompt(relative_path: str) -> str:
    return (ROOT / "prompts" / relative_path).read_text(encoding="utf-8")


def _with_pdca_spirit(template: str) -> str:
    """Inject one shared judgment discipline without creating another workflow."""
    return f"{_read_prompt('pdca_spirit.txt').rstrip()}\n\n{template.lstrip()}"


def _load_capability_focus(profile: str) -> str:
    fallback = "[Capability Focus] General software requirement analysis."
    profiles_path = ROOT / "resources" / "templates" / "profiles.json"
    try:
        profiles_data = json.loads(profiles_path.read_text(encoding="utf-8"))
        profile_data = profiles_data.get(profile)
        if not isinstance(profile_data, dict):
            logger.warning(f"Unknown capability profile '{profile}'; using general analysis")
            return fallback
        prompt_filename = profile_data.get("prompt_file", f"{profile}.txt")
        expert_path = ROOT / "prompts" / "profiles" / prompt_filename
        if not expert_path.exists():
            logger.warning(f"Expert persona file not found for profile '{profile}': {expert_path}")
            return fallback
        focus = expert_path.read_text(encoding="utf-8")
        return (
            focus.replace("[Role]", "[Capability Focus]")
            .replace("[Best Fit]", "[Apply When]")
            .replace("[Coverage]", "[Focus]")
            .replace("[Secondary Competence]", "[Secondary Coverage]")
            .replace("[Boundaries]", "[Limits]")
        )
    except (OSError, json.JSONDecodeError, TypeError) as error:
        logger.warning(f"Failed to load expert persona '{profile}': {error}")
        return fallback


def _load_profile_policy() -> str:
    policy_path = ROOT / "resources" / "policies" / "profile-policy.json"
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        return json.dumps(policy, ensure_ascii=False)
    except (OSError, json.JSONDecodeError, TypeError) as error:
        logger.error(f"Failed to load profile policy: {error}")
        return "{}"

def discovery_prompt(available_templates_json: str = "{}") -> str:
    """Return the consultant contract for building the initial requirement boundary map."""
    logger.info("[PROMPT] Loading consultant discovery contract")
    template = _with_pdca_spirit(_read_prompt("discovery.txt"))
    return (
        template
        .replace("{available_templates_json}", available_templates_json)
        .replace("{profile_policy_json}", _load_profile_policy())
    )


def consultant_plan_review() -> str:
    """Return the release-gate contract for filtering an initial plan before display."""
    logger.info("[PROMPT] Loading consultant plan release-gate contract")
    return _with_pdca_spirit(_read_prompt("consultant_plan_review.txt")).replace(
        "{profile_policy_json}", _load_profile_policy()
    )

def requirement_interview(
    profile: str,
) -> str:
    """Return one consultant answer-review contract with a focused capability."""
    logger.info(f"[PROMPT] Loading consultant answer review with capability={profile}")
    template = _with_pdca_spirit(_read_prompt("requirement_interview.txt"))
    return template.replace("{capability_focus}", _load_capability_focus(profile))


def consultant_reconciliation() -> str:
    """Return the consultant contract for cross-domain reconciliation and next routing."""
    logger.info("[PROMPT] Loading consultant reconciliation contract")
    return _read_prompt("consultant_reconciliation.txt")

def batch_audit_draft(profile: str = "simple") -> str:
    """Return the bounded contract for the final Requirement Batch Audit (Stage A)."""
    logger.info(f"[PROMPT] Loading 'batch_audit_draft' with profile={profile}")
    template = _with_pdca_spirit(_read_prompt("batch_audit_draft.txt"))
    return template.replace("{profile}", profile)

def technical_alignment_draft(
    profile: str = "simple",
    capability_profiles: list[str] | None = None,
) -> str:
    """Return the bounded contract for planning a technical alignment draft."""
    capability_profiles = list(dict.fromkeys(capability_profiles or []))
    logger.info(
        "[PROMPT] Loading 'technical_alignment_draft' "
        f"with profile={profile} capabilities={capability_profiles}"
    )
    template = _with_pdca_spirit(_read_prompt("technical_alignment_draft.txt"))
    capability_focus = "\n\n".join(
        f"Capability source `{capability}`:\n{_load_capability_focus(capability)}"
        for capability in capability_profiles
    )
    if not capability_focus:
        capability_focus = "[Capability Focus] General software architecture analysis."
    capability_boundary = (
        "[Architecture Capability Boundary - Single Pass]\n"
        "Treat the following material as one combined skill boundary, not as "
        "personas or sequential role changes.\n\n"
        f"{capability_focus}"
    )
    return (
        template.replace("{profile}", profile)
        .replace("{capability_boundary}", capability_boundary)
    )


def iso_audit_draft() -> str:
    """Return the bounded role contract for an ISO-aligned audit draft."""
    logger.info("[PROMPT] Loading ISO-aligned audit draft contract")
    return _with_pdca_spirit(_read_prompt("iso_audit_draft.txt"))


def system_design_draft() -> str:
    """Return the future system-design draft contract; deterministic Tools remain pending."""
    logger.info("[PROMPT] Loading system-design draft contract")
    return _read_prompt("system_design_draft.txt")


def pm_contract_draft() -> str:
    """Return the future PM-contract draft contract; deterministic Tools remain pending."""
    logger.info("[PROMPT] Loading PM-contract draft contract")
    return _read_prompt("pm_contract_draft.txt")
