# PxDCA input, state, output, and log boundary

## Input

The Client selects one of four public Tools. Natural-language generation inside
the three development workflows is requested through MCP Sampling; the Server
owns sequencing and validation. `generate_skill` reads the canonical
`tools/SKILL.md`; only its optional optimized mode requests Sampling.

## State

- Default path: `data/state/`
- Override: `PXDCA_STATE_ROOT`
- Key: the `session_id` returned by `generate_requirements`
- Storage: one atomically replaced JSON file per requirement workflow

State is independent of an HTTP, stdio, VS Code, or other MCP connection. The
state directory must be on persistent storage when the Server runs in a
container.

## Output

- Default root: `PXDCA_ARTIFACT_ROOT`, normally `data/artifacts/`
- Default workflow directory: `data/artifacts/<session_id>/`
- A relative `output_dir` must remain inside `PXDCA_ARTIFACT_ROOT`.
- Absolute `output_dir` values are rejected.
- Tool-level overrides are disabled unless `artifacts.allow_tool_override=true`.

Generated artifacts are stored with the session so repeated completed calls are
idempotent. File generation can be disabled with `artifacts.enabled=false`; the
validated document remains available in the MCP result and persistent session.

Skill output is independent of requirement state:

- Default directory: `data/artifacts/pxdca-pdca/`
- Filename: `SKILL.md`
- `generate_skill` never creates or updates `PXDCA_STATE_ROOT`.

## Logs

`data/logs/` records Server startup, requests, workflow stages, validation
outcomes, and errors. Session files contain user requirement content and must
not be copied into logs.
