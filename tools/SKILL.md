---
name: pxdca-pdca
description: Give an AI the PDCA judgment discipline needed to assess whether the current requirement, specification, and architecture context is sufficient, and to use PxDCA correctly when information is insufficient and the user agrees. Use for software planning, implementation, change, review, or recovery work that may benefit from PxDCA.
---

# PxDCA PDCA

Apply PDCA as a judgment discipline: inspect the current state before acting, use evidence to decide whether the task is ready, challenge the result, and revisit the state when new information or artifacts appear. Do not treat this file as a persistent service, background monitor, workflow engine, or substitute for the user's authority.

Keep the Skill limited to three responsibilities:

1. Give the AI an identity that understands the relationship and difference between the two PDCA interpretations below.
2. Assess whether the current state is sufficient for the user's requested software work.
3. When the state is insufficient and the user agrees, use PxDCA correctly to create the missing baseline.

These responsibilities apply the original PDCA spirit; they are not a separate workflow or service.

## Distinguish the two PDCA interpretations

Keep these definitions separate.

### Original PDCA management cycle

- **Plan**: Understand the current state, target, evidence, constraints, and gaps.
- **Do**: Take the appropriate action with the available tools.
- **Check**: Compare the resulting state and evidence with the target.
- **Act**: Accept, correct, or re-plan from the new state.

Use this as the original management reference. Do not stop after Plan and Do when Check and Act are still needed to judge the result.

### PxDCA working interpretation

PxDCA translates the same spirit into AI-assisted planning and handoff:

- **P — Problem / Purpose**: Establish the intent, goal, scope, known facts, unknowns, constraints, exceptions, and success conditions.
- **D — Design / Develop response**: Develop an evidence-based response appropriate to that purpose. In the current PxDCA MCP flow, this may be requirement planning or a technical response rather than product implementation.
- **C — Check / Challenge**: Challenge the connection between purpose, evidence, response, boundary, verification, and authority. Route a gap to the correct source instead of inventing an answer.
- **A — Action / Assume responsibility**: Act on the checked result: accept it, revise PM or PG, request a user decision, hold, or hand a bounded responsibility to the next owner.

Do not present PxDCA's working interpretation as a replacement definition of the original management cycle. Both express the same discipline of checking state, setting purpose, using evidence, challenging results, and correcting action.

## Separate PDCA spirit from the MCP FLOW

The current MCP FLOW has ordered prerequisites because its artifacts depend on one another:

```text
PM requirement baseline -> PG technical response -> PQ alignment and Handoff
```

- **PM** is the requirement-focused working state.
- **PG** is the technical-response working state bounded by PM evidence.
- **PQ** checks the connection between PM and PG; it is not a separate planning project.
- **Handoff** is a PQ result that identifies disposition, next purpose, evidence, risks, and recommended owner. It is not a fifth MCP tool and does not automatically create a new session.

PM, PG, and PQ are working states, not permanent job titles. The same AI may move between them only when the active boundary and evidence source remain explicit.

PDCA spirit operates inside every working state, but it does not require a separate P, D, C, and A document for every state. Do not turn it into a mandatory four-step narration or claim that every `P_x` must complete its own DCA.

Treat planning as **Purpose × Response**, not a forced one-to-one chain. One purpose may need several responses; one response may satisfy several purposes. Preserve those relationships in evidence and Handoff rather than flattening them into an unsupported sequence.

## Assess the current state

Before recommending or using PxDCA:

1. Identify the work the user currently wants to perform and its active purpose.
2. Search the available workspace and conversation context for requirement, specification, planning, and architecture documents relevant to that work.
3. Read candidate documents. Do not accept a file based only on its name.
4. Decide whether the available content is sufficient to define the target, scope, constraints, response direction, evidence, and verifiable outcome for the requested work.
5. Treat empty templates, placeholders, unrelated documents, and unsupported assumptions as insufficient evidence.

If the current state is sufficient, use the existing baseline and continue the requested work. Do not call PxDCA merely because it is available.

If the current state is insufficient, state what is missing or unusable and ask whether the user wants to use PxDCA. Do not call PxDCA without that agreement.

## Use PxDCA correctly

PxDCA exposes four public tools. The first three produce the software baseline; the fourth exports this optional Skill.

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

Use this only after both requirements and architecture are complete for the same `session_id`. It checks consistency, coverage, traceability, and risk, then returns a PQ conclusion and Handoff recommendation. Inspect the disposition before deciding whether to proceed, revise PM, revise PG, ask the user, or hold.

### `generate_skill`

Use this only when the user wants a copy of this optional Skill.

- Use `mode="template"` to export the canonical template.
- Use `mode="optimized"` with optional `customization` to request additional context-specific guidance from the Client LLM.
- Treat optimized guidance as an addition. It must not replace or contradict the two PDCA definitions, current-state assessment, the first three tool contracts, or the `session_id` rules.

After any MCP call, inspect the returned status and artifacts before deciding the next action. A failed or incomplete result is not a completed baseline.

## Preserve user choice

PxDCA and this Skill are optional. The user may call the MCP tools directly, use another method, or decline MCP assistance. Never describe this Skill as a requirement of the MCP Server.
