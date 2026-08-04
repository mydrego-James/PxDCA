# LogicMCP Server (FastMCP 3)

This package is the deployable product core. It registers LogicMCP Prompts,
Resources, and deterministic Tools and serves them over MCP.

From the repository root, the supported Windows entrypoint is:

```powershell
.\run.bat
```

FastMCP users can also inspect or run the project through `fastmcp.json`:

```powershell
$env:PYTHONUTF8 = "1"
fastmcp inspect fastmcp.json
fastmcp run fastmcp.json
```

The equivalent Python module entrypoint is:

```powershell
$env:MCP_HOST = "127.0.0.1"
$env:MCP_PORT = "8000"
$env:MCP_PATH = "/mcp"
$env:MCP_TRANSPORT = "http"
python -m server.fastmcp_service
```

Endpoint: `http://127.0.0.1:8000/mcp`.

Relative paths passed to file-producing MCP Tools are resolved under the root
`output/` directory. A Factory or another client may pass an absolute path when
it owns the destination. Root `logs/` is reserved exclusively for MCP Server
activity.

See `docs/IO_BOUNDARY.md` for the complete Factory/MCP input, output, and log
ownership rule.

This package does not import the optional Python Factory, CLI/API adapters, or
LLM providers. Workflow orchestration examples are described in
`docs/WORKFLOW.md`.
