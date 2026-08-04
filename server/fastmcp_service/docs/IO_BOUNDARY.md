# LogicMCP input, output, and log boundary

## Ownership

- Factory/APP/CLI owns user input, session state, LLM interaction, and the
  destination selected for a Factory workflow.
- LogicMCP Server owns MCP validation and deterministic rendering. A renderer
  remains an MCP Tool even when the Factory selected its destination.
- Root `logs/` belongs only to LogicMCP Server operations.
- Root `output/` is the default destination owned by LogicMCP Server.
- `factory/runtime/` belongs only to the separate optional Factory project.

## Output path rule

The public MCP Tool arguments remain unchanged:

- A relative `output_dir` or `output_path` is resolved below root `output/`.
- An absolute path is treated as a client-owned destination. This lets Factory
  keep its artifacts under `factory/runtime/output/` without coupling MCP to
  Factory internals.
- A relative path may not traverse outside root `output/`.

This preserves both valid flows:

```text
MCP client -> relative path -> LogicMCP root output/
Factory -> absolute Factory destination -> MCP renderer -> Factory runtime/output/
```

## Log rule

`logs/fastmcp/` records LogicMCP startup, shutdown, HTTP request/response
status, validation evidence, and MCP Tool execution. Request and response
bodies are not copied into HTTP access logs; Tool validation logs retain the
existing bounded evidence and hashes.

Factory, CLI, adapter, and LLM logs are written below
`factory/runtime/logs/` instead.
