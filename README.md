# LogicMCP Server

This repository's deployable product is LogicMCP Server, implemented with the
FastMCP framework for traceable requirement discovery, technical alignment,
and ISO-aligned process checking. It contains no LLM and starts no CLI.

## Install and run

```powershell
.\install.bat
.\run.bat
```

The service listens on:

```text
http://127.0.0.1:8000/mcp
```

`run.bat` performs a first-run installation when necessary. The root
`requirements.txt`, `Dockerfile`, and `compose.yaml` contain only the FastMCP
service boundary.

## Optional Factory project

The repository also keeps a replaceable local execution chain for testing the
MCP without an IDE:

```text
future APP -> CLI/API adapter -> Python Factory -> LLM adapter -> MCP service
```

Install and run that optional chain separately, after the MCP service is
running:

```powershell
.\factory\cli\install.bat
.\factory\cli\run.bat
```

The factory exposes stable contracts and runtime builders from `factory/`.
Adapters, LLM providers, and the MCP implementation remain separate. A custom
CLI or API adapter only needs to preserve the Factory boundary; it does not
need to duplicate LLM-to-MCP transmission logic.

The code under `factory/adapters/app_prototype/` is parked prototype material.
There is no supported APP adapter yet.

## Directory boundaries

```text
server/fastmcp_service/          deployable MCP service package
  prompts/                       LLM prompt contracts exposed by MCP
  resources/                     schemas, policies, and templates
  tools/                         deterministic MCP tools
factory/                         optional Python workflow factory
  contracts.py                   stable adapter/factory data contracts
  controller/                    workflow sequencing and MCP client port
  llm/                           replaceable LLM adapters
  composition/                   dependency assembly only
  adapters/cli/                  replaceable terminal adapter
  adapters/app_prototype/        parked, unsupported APP prototype
  cli/                           separate no-IDE CLI project and installer
  runtime/                       Factory-owned logs, state, input, and output
tools/                           MCP inspection/tuning/backup/update utilities
logs/                            MCP Server logs only
output/                          default MCP-owned file output
tests/                           behavior and dependency-boundary tests
```

Dependency rules:

- `server/fastmcp_service/` never imports `factory/` or root `tools/`.
- root `tools/` never contains user-facing Factory/CLI entrypoints.
- root `logs/` is owned exclusively by the MCP Server.
- `factory/llm/` never imports MCP service internals.
- `factory/controller/` reaches MCP only through its gateway and LLM only
  through `BaseLLMClient`.
- adapters consume Factory contracts and builders; they do not own workflow
  sequencing.
- root installation and startup never install or start CLI, APP, or LLM code.

See [INSTALL.MD](INSTALL.MD) for deployment and tool configuration, and
[MAP.MD](MAP.MD) for the maintenance index.
