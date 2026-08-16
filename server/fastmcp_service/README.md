# LogicMCP FastMCP service

This package registers three persistent workflows and one Skill exporter:

- `generate_requirements`
- `generate_architecture`
- `run_audit`
- `generate_skill`

`public_tools.py` is the only MCP registration module. `workflow_service.py`
owns orchestration and persistent sessions. `skill_service.py` exports the
canonical `tools/SKILL.md` without creating a requirement session. Prompt
templates, policies, schemas, validators, and renderers are private
implementation details.

Runtime entry:

```text
python -m server.fastmcp_service
> __main__.py
> server.py
> mcp_instance.py + public_tools.py
```

See `docs/WORKFLOW.md` for phase chains and `docs/IO_BOUNDARY.md` for state and
filesystem boundaries.
