# LogicMCP Server installation

The supported installation deploys one local Streamable HTTP MCP service. It
does not install an LLM, enter a CLI, or start an APP.

## Windows quick start

From the repository root:

```powershell
.\install.bat
.\run.bat
```

`install.bat` creates `.venv` and installs only `requirements.txt`.
`run.bat` starts:

```text
http://127.0.0.1:8000/mcp
```

Leave that terminal open while MCP clients are connected. On first use,
`run.bat` automatically calls `install.bat` if `.venv` is absent.

## Manual startup

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:MCP_HOST = "127.0.0.1"
$env:MCP_PORT = "8000"
$env:MCP_PATH = "/mcp"
$env:MCP_TRANSPORT = "http"
$env:MCP_OUTPUT_ROOT = ".\output"
.\.venv\Scripts\python.exe -m server.fastmcp_service
```

The FastMCP package contains Prompts, Resources, and deterministic Tools. It has
no provider key or LLM configuration requirement.

## MCP client configuration

Use the local endpoint in an MCP client. For Codex `config.toml`, for example:

```toml
[mcp_servers.fastmcp]
url = "http://127.0.0.1:8000/mcp"
```

Other hosts should use their equivalent Streamable HTTP MCP configuration.

## Docker

The root image and Compose service are MCP-only:

```powershell
docker build -t local-fastmcp .
docker run --rm -p 8000:8000 local-fastmcp
```

or:

```powershell
docker compose up --build mcp
```

The container binds internally to `0.0.0.0:8000`; the published local endpoint
remains `http://127.0.0.1:8000/mcp`.

## Optional Factory CLI project

This is a separate test installation. Start the MCP service first in one
terminal, then use a second terminal:

```powershell
.\factory\cli\install.bat
.\factory\cli\run.bat
```

The Factory CLI installer creates `factory\cli\.venv` and
`factory\cli\.env`. Configure the LLM only in `factory\cli\.env`.

Offline OpenAI-compatible example:

```dotenv
MCPS_URL=http://127.0.0.1:8000/mcp
LLM_MODE=offline
LOCAL_PROVIDER=openai_compatible
LOCAL_MODEL=google/gemma-3-4b
LOCAL_API_KEY=lm-studio
LOCAL_API_URL=http://127.0.0.1:1234/v1/chat/completions
```

Online example:

```dotenv
MCPS_URL=http://127.0.0.1:8000/mcp
LLM_MODE=online
NETWORK_PROVIDER=google_genai
NETWORK_MODEL=gemini-3.6-flash
NETWORK_API_KEY=replace-with-your-key
```

Audit test entrypoint:

```powershell
.\factory\cli\run.bat audit
```

The CLI is an Adapter. It calls the stable Factory surface in `factory/`; it
does not implement LLM-to-MCP workflow transmission itself. A replacement CLI
or API should consume `factory/contracts.py` and the builders exported by
`factory/__init__.py`.

## APP status

No supported APP is currently built. `factory/adapters/app_prototype/` contains
parked prototype material only. It is not registered, installed, or started by
the supported commands.

## Troubleshooting

### Port 8000 is unavailable

Stop the process already listening on port 8000, then run `run.bat` again. The
supported Windows launcher intentionally uses `127.0.0.1:8000`.

### CLI cannot reach MCP

Confirm `run.bat` is still running and that `MCPS_URL` in
`factory\cli\.env` is
`http://127.0.0.1:8000/mcp`.

### MCP works but an LLM call fails

The MCP service and LLM are independent. Check only `factory\cli\.env` and the
chosen provider or local model server; no FastMCP reinstall is required.
