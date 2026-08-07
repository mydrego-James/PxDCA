# LogicMCP Server public-surface audit

Audit date: 2026-08-06

## Public contract

- Tools: 3
- Prompts: 0
- Resources: 0
- Baseline: `contract-baseline.json`

Public Tools:

1. `generate_requirements`
2. `generate_architecture`
3. `run_audit`

## Registration boundary

- `server.py` imports `public_tools.py` only for endpoint registration.
- `prompts.py` contains private prompt loaders without MCP decorators.
- `resources.py` contains private resource loaders without MCP decorators.
- `tools/` contains private validators and renderers without MCP decorators.

## Workflow ownership

- Client chooses one of the three business methods.
- Server owns all internal phase routing and deterministic validation.
- Server requests language generation through MCP Sampling.
- Requirement interview state is stored below `MCP_STATE_ROOT` and is not tied
  to a transport connection.

## Contract corrections

- Removed public access to internal validators and renderers.
- Removed public Prompt and Resource registration.
- Replaced stringified `payload_json` public parameters with explicit workflow
  parameters.
- Mapped audit `findings` and `conclusion` fields into the audit renderer's
  major/other finding sections and conclusion output.

## Verification

- In-memory MCP initialize/list: 3 Tools, 0 Prompts, 0 Resources.
- Python compile: passed.
- Deterministic Sampling smoke test: Q0 generated Q1..Q3.
- Client disconnect/reconnect test: the same `session_id` resumed at Q2.
- Requirement, architecture, and audit artifact generation: passed.
- Persisted final phase: `audit_completed`.
