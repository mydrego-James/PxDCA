# LogicMCP_Server → PxDCA migration

The project is now officially named **PxDCA**. New documentation, service metadata,
paths, Docker resources, environment variables, and the canonical Skill use that
name.

## Runtime settings

Use `config/pxdca.toml` for non-secret settings and `PXDCA_*` variables for runtime
overrides. The former `MCP_HOST`, `MCP_PORT`, `MCP_PATH`, `MCP_TRANSPORT`,
`MCP_STATE_ROOT`, and `MCP_OUTPUT_ROOT` variables are read only as deprecated
fallbacks and generate a warning.

| Previous | Current |
|---|---|
| `MCP_HOST` | `PXDCA_HOST` |
| `MCP_PORT` | `PXDCA_PORT` |
| `MCP_PATH` | `PXDCA_PATH` |
| `MCP_TRANSPORT` | `PXDCA_TRANSPORT` |
| `MCP_STATE_ROOT` | `PXDCA_STATE_ROOT` |
| `MCP_OUTPUT_ROOT` | `PXDCA_ARTIFACT_ROOT` |

The former Compose-only `LOGICMCP_*` variables are no longer official settings.
Use the `PXDCA_*` variables in `.env.example`.

## Data paths

The previous default combined session state and generated files below `output/`.
PxDCA separates them:

```text
data/state/       persistent requirement sessions
data/artifacts/   optional generated Markdown and JSON
data/logs/        service and HTTP logs
```

Existing sessions are not moved or deleted automatically. If sessions remain in
`output/.logicmcp/sessions`, temporarily set `PXDCA_STATE_ROOT` to that absolute
directory or copy the JSON files into `data/state` while the server is stopped.

## Skill

The canonical Skill name is now `pxdca-pdca`. The old `logicmcp-pdca` name is not
the official invocation name. Users who customized the Skill name should continue
to invoke their chosen name.
