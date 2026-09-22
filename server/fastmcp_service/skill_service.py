"""Generate an optional PxDCA Skill without changing requirement sessions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp import Context

from .mcp_instance import OUTPUT_ROOT, ROOT, logger
from .settings import settings


TEMPLATE_PATH = ROOT / "tools" / "SKILL.md"
VALID_MODES = {"template", "optimized"}
REQUIRED_CORE_MARKERS = {
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
}


class SkillGenerationError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _resolve_output_dir(value: str) -> Path:
    if value.strip() and not settings.artifacts.allow_tool_override:
        raise SkillGenerationError(
            "OUTPUT_OVERRIDE_DISABLED",
            "output_dir 已由 PxDCA 外部設定管理；如需開放 Tool 覆寫，請設定 allow_tool_override。",
        )
    requested = Path(value.strip()) if value.strip() else Path("pxdca-pdca")
    if requested.is_absolute():
        raise SkillGenerationError("INVALID_OUTPUT_DIR", "output_dir 不可使用絕對路徑。")
    resolved = (OUTPUT_ROOT / requested).resolve()
    if resolved != OUTPUT_ROOT and OUTPUT_ROOT not in resolved.parents:
        raise SkillGenerationError(
            "INVALID_OUTPUT_DIR",
            "相對 output_dir 必須位於 PxDCA artifact root 之內。",
        )
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _canonical_template() -> str:
    try:
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
    except OSError as error:
        raise SkillGenerationError(
            "SKILL_TEMPLATE_UNAVAILABLE",
            "Server 無法讀取 canonical tools/SKILL.md。",
        ) from error
    missing = sorted(marker for marker in REQUIRED_CORE_MARKERS if marker not in content)
    if missing:
        raise SkillGenerationError(
            "SKILL_TEMPLATE_INVALID",
            "Canonical SKILL.md 缺少必要核心內容：" + ", ".join(missing),
        )
    return content


def _clean_markdown(value: str) -> str:
    candidate = value.strip()
    if candidate.startswith("```markdown") or candidate.startswith("```md"):
        lines = candidate.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        candidate = "\n".join(lines).strip()
    return candidate


async def _optimized_addition(
    ctx: Context,
    *,
    canonical: str,
    customization: str,
) -> str:
    system_prompt = """You add optional, context-specific guidance to an existing AI Skill.
Return Markdown body content only: no YAML frontmatter and no code fence.
Do not redefine, replace, or contradict the canonical rules.
Do not change the meanings of original Plan-Do-Check-Act or PxDCA's
Problem/Purpose-Design-Check/Challenge-Action model. Do not change the names,
parameters, prerequisites, or session behavior of generate_requirements,
generate_architecture, run_audit, or generate_skill. Do not claim the Skill is
a persistent service, monitor, workflow engine, or required MCP dependency.
Keep the addition concise and useful for the requested context."""
    request = (
        "Canonical Skill:\n\n"
        + canonical
        + "\n\nRequested customization:\n"
        + (customization.strip() or "Improve applicability without changing the core rules.")
    )
    try:
        sampled = await ctx.sample(
            request,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=2048,
        )
    except Exception as error:
        raise SkillGenerationError(
            "CLIENT_SAMPLING_REQUIRED",
            "optimized 模式需要 MCP Client 支援 LLM Sampling。",
        ) from error
    addition = _clean_markdown(sampled.text)
    if not addition:
        raise SkillGenerationError(
            "EMPTY_OPTIMIZATION",
            "Client LLM 未產生可用的 Skill 補充內容。",
        )
    return addition


async def generate_skill_document(
    ctx: Context,
    *,
    mode: str,
    customization: str,
    output_dir: str,
) -> dict[str, Any]:
    try:
        if mode not in VALID_MODES:
            raise SkillGenerationError(
                "INVALID_MODE",
                "mode 必須是 template 或 optimized。",
            )
        canonical = _canonical_template().rstrip() + "\n"
        content = canonical
        if mode == "optimized":
            addition = await _optimized_addition(
                ctx,
                canonical=canonical,
                customization=customization,
            )
            content += (
                "\n## Optional optimized guidance\n\n"
                "This section may add context but cannot override the canonical rules above.\n\n"
                + addition.rstrip()
                + "\n"
            )
        artifact = None
        if settings.artifacts.enabled:
            target = _resolve_output_dir(output_dir) / "SKILL.md"
            try:
                target.write_text(content, encoding="utf-8", newline="\n")
            except OSError as error:
                raise SkillGenerationError(
                    "SKILL_OUTPUT_FAILED",
                    "Server 無法寫入 SKILL.md。",
                ) from error
            artifact = {"kind": "skill", "path": str(target)}
            logger.info("[SKILL] generated mode=%s path=%s", mode, target)
        return {
            "status": "completed",
            "workflow": "skill_generation",
            "mode": mode,
            "artifact": artifact,
            "content": content,
        }
    except SkillGenerationError as error:
        logger.warning("[SKILL] generation failed code=%s message=%s", error.code, error)
        return {
            "status": "failed",
            "workflow": "skill_generation",
            "mode": mode,
            "error": {"code": error.code, "message": str(error), "recoverable": False},
        }
