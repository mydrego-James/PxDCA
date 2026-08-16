# LogicMCP input, state, output, and log boundary

## Input

The Client selects one of four public Tools. Natural-language generation inside
the three development workflows is requested through MCP Sampling; the Server
owns sequencing and validation. `generate_skill` reads the canonical
`tools/SKILL.md`; only its optional optimized mode requests Sampling.

## State

- Default path: `output/.logicmcp/sessions/`
- Override: `MCP_STATE_ROOT`
- Key: the `session_id` returned by `generate_requirements`
- Storage: one atomically replaced JSON file per requirement workflow

State is independent of an HTTP, stdio, VS Code, or other MCP connection. The
state directory must be on persistent storage when the Server runs in a
container.

## Output

- Default root: `MCP_OUTPUT_ROOT`, normally `./output/`
- Default workflow directory: `output/<session_id>/`
- A relative `output_dir` must remain inside `MCP_OUTPUT_ROOT`.
- An absolute `output_dir` is treated as an explicitly selected destination.

Generated artifacts are stored with the session so repeated completed calls are
idempotent.

Skill output is independent of requirement state:

- Default directory: `output/logicmcp-pdca/`
- Filename: `SKILL.md`
- `generate_skill` never creates or updates `MCP_STATE_ROOT`.

## Logs

`logs/fastmcp/` records Server startup, requests, workflow stages, validation
outcomes, and errors. Session files contain user requirement content and must
not be copied into logs.
