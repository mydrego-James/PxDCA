"""The complete public MCP surface: three workflows and one Skill exporter."""

from typing import Literal

from fastmcp import Context

from .mcp_instance import mcp
from .skill_service import generate_skill_document
from .workflow_service import audit_workflow, architecture_workflow, requirements_workflow


@mcp.tool(
    name="generate_requirements",
    description=(
        "需求書唯一入口。新工作提供 q0；Server 產生並持久化 Q1..Qn。"
        "續答提供 session_id 與 answer；只提供 session_id 可在中斷或隔天後查詢並接續。"
        "內部生成、驗證、狀態轉移與文件渲染皆為封閉流程。"
    ),
)
async def generate_requirements(
    ctx: Context,
    q0: str = "",
    session_id: str = "",
    answer: str = "",
    profile: Literal["simple", "professional", "consultant"] = "professional",
    output_dir: str = "",
) -> dict:
    return await requirements_workflow(
        ctx,
        q0=q0,
        session_id=session_id,
        answer=answer,
        profile=profile,
        output_dir=output_dir,
    )


@mcp.tool(
    name="generate_architecture",
    description=(
        "架構書唯一入口。使用已完成需求書的 session_id；Server 內部完成技術規劃、"
        "需求對齊驗證與架構文件渲染。"
    ),
)
async def generate_architecture(
    ctx: Context,
    session_id: str,
    output_dir: str = "",
) -> dict:
    return await architecture_workflow(ctx, session_id=session_id, output_dir=output_dir)


@mcp.tool(
    name="run_audit",
    description=(
        "稽核唯一入口。使用已完成需求書與架構書的 session_id；Server 內部完成"
        "一致性、覆蓋、追溯與風險稽核並產生報告。"
    ),
)
async def run_audit(
    ctx: Context,
    session_id: str,
    output_dir: str = "",
) -> dict:
    return await audit_workflow(ctx, session_id=session_id, output_dir=output_dir)


@mcp.tool(
    name="generate_skill",
    description=(
        "產生可選的 LogicMCP SKILL.md。template 模式輸出 Server canonical 模板；"
        "optimized 模式透過 Client LLM Sampling 附加情境化指引，但固定保留兩種 PDCA"
        "差異、前三個 Tool 的用途與 session_id 接續規則。此 Tool 不建立需求 session。"
    ),
)
async def generate_skill(
    ctx: Context,
    mode: Literal["template", "optimized"] = "template",
    customization: str = "",
    output_dir: str = "",
) -> dict:
    return await generate_skill_document(
        ctx,
        mode=mode,
        customization=customization,
        output_dir=output_dir,
    )


__all__ = [
    "generate_requirements",
    "generate_architecture",
    "run_audit",
    "generate_skill",
]
