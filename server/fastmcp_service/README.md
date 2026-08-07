# LogicMCP FastMCP service

This package registers three public MCP Tools and owns their complete workflows:

- `generate_requirements`
- `generate_architecture`
- `run_audit`

`public_tools.py` is the only MCP registration module. `workflow_service.py`
owns orchestration and persistent sessions. Prompt templates, policies, schemas,
validators, and renderers are private implementation details.

Runtime entry:

```text
python -m server.fastmcp_service
> __main__.py
> server.py
> mcp_instance.py + public_tools.py
```

See `docs/WORKFLOW.md` for phase chains and `docs/IO_BOUNDARY.md` for state and
filesystem boundaries.
