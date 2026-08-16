---
name: logicmcp-pdca
description: Guide an AI to distinguish traditional Plan-Do-Check-Act from LogicMCP's project-specific Problem/Purpose-Design-Check/Challenge-Action model, assess whether current requirement, specification, and architecture context is sufficient for the requested software work, and correctly use LogicMCP when information is insufficient and the user agrees. Use for software planning, implementation, change, review, or recovery work that may benefit from LogicMCP.
---

# LogicMCP PDCA

Apply the original PDCA spirit to the current task. Inspect the current state before acting, use evidence to decide whether the task is ready, and revisit the state after new information or artifacts are produced. Do not treat this file as a persistent service, background monitor, or workflow engine.

Keep the Skill limited to three responsibilities:

1. Give the AI an identity that understands the difference between the two PDCA meanings below.
2. Assess whether the current state is sufficient for the user's requested software work.
3. When the state is insufficient and the user agrees, use LogicMCP correctly to create the missing baseline.

These responsibilities apply the original PDCA spirit; they are not a separate workflow or service.

## Distinguish the two PDCA meanings

Keep these definitions separate.

### Original PDCA spirit

- **Plan**: Understand the current state, target, evidence, constraints, and gaps.
- **Do**: Take the appropriate action with the available tools.
- **Check**: Compare the resulting state and evidence with the target.
- **Act**: Accept, correct, or re-plan from the new state.

Use this as a way of working. Do not stop after Plan and Do when Check and Act are still needed to judge the result.

### LogicMCP project definition

LogicMCP borrows the idea of a cycle but defines its letters for software development and AI work:

- **P — Problem / Purpose**: Confirm the real problem, goal, scope, known facts, unknowns, constraints, exceptions, and success conditions before choosing technology.
- **D — Design**: Convert confirmed requirements into system boundaries, functional design, technical choices, data flow, module responsibilities, inputs, outputs, execution steps, validation, risks, and alternatives.
- **C — Check / Challenge**: Challenge the design for omissions, unauthorized scope, contradictions, incorrect sources, incomplete boundaries, feasibility, verification, and traceability; return to P or D when necessary.
- **A — Action**: Hand the confirmed design to the responsible developer, engineer, AI Agent, tester, service, or automation for implementation, testing, delivery, and result recording.

Do not present the LogicMCP definition as the original management PDCA. Use the original PDCA spirit to assess and improve the current task; use the LogicMCP definition to understand the software artifacts produced by LogicMCP.

## Assess the current state

Before recommending or using LogicMCP:

1. Identify the software work the user currently wants to perform.
2. Search the available workspace and conversation context for requirement, specification, planning, and architecture documents relevant to that work.
3. Read candidate documents. Do not accept a file based only on its name.
4. Decide whether the available content is sufficient to define the target, scope, constraints, design direction, and verifiable outcome for the requested work.
5. Treat empty templates, placeholders, unrelated documents, and unsupported assumptions as insufficient evidence.

If the current state is sufficient, use the existing baseline and continue the requested work. Do not call LogicMCP merely because it is available.

If the current state is insufficient, state what is missing or unusable and ask whether the user wants to use LogicMCP. Do not call LogicMCP without that agreement.

## Use LogicMCP correctly

LogicMCP exposes four public tools. The first three produce the software baseline; the fourth exports this optional Skill.

### `generate_requirements`

Use this as the only requirements entry point.

- Start a new requirement interview with `q0` and an optional `profile`: `simple`, `professional`, or `consultant`.
- Preserve the returned `session_id`.
- Continue an interview with the same `session_id` plus the user's `answer`.
- Resume or inspect an interrupted interview by sending only `session_id`.
- Do not start a new session when a valid existing session can be resumed.

### `generate_architecture`

Use this only after `generate_requirements` has completed for the same `session_id`. It generates an architecture document aligned with the completed requirements.

### `run_audit`

Use this only after both requirements and architecture are complete for the same `session_id`. It checks consistency, coverage, traceability, and risk and produces the audit artifacts.

### `generate_skill`

Use this only when the user wants a copy of this optional Skill.

- Use `mode="template"` to export the canonical template.
- Use `mode="optimized"` with optional `customization` to request additional context-specific guidance from the Client LLM.
- Treat optimized guidance as an addition. It must not replace or contradict the two PDCA definitions, current-state assessment, the first three tool contracts, or the `session_id` rules.

After any MCP call, inspect the returned status and artifacts before deciding the next action. A failed or incomplete result is not a completed baseline.

## Preserve user choice

LogicMCP and this Skill are optional. The user may call the MCP tools directly, use another method, or decline MCP assistance. Never describe this Skill as a requirement of the MCP Server.
