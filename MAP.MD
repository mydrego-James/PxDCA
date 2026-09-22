# PxDCA Server — Project Map

## Root tree

```text
PxDCA/
├─ server/
│  ├─ __init__.py
│  ├─ entrypoint.py
│  └─ fastmcp_service/
├─ tools/
│  ├─ README.md
│  ├─ PLAN.md
│  └─ SKILL.md
├─ config/
│  ├─ pxdca.toml
│  └─ pxdca.example.toml
├─ scripts/
│  └─ bootstrap.py
├─ data/                       # runtime only; ignored by Git
│  ├─ state/
│  ├─ artifacts/
│  └─ logs/
├─ .dockerignore
├─ .env.example
├─ .python-version
├─ .gcloudignore
├─ .gitattributes
├─ .gitignore
├─ compose.yaml
├─ docker.md
├─ Dockerfile
├─ fastmcp.json
├─ install.bat
├─ install.sh
├─ MIGRATION.md
├─ MAP.MD
├─ README.md
├─ requirements.txt
├─ run.bat
└─ run.sh
```

## Server tree

```text
server/
├─ __init__.py
├─ entrypoint.py
└─ fastmcp_service/
   ├─ __init__.py
   ├─ __main__.py
   ├─ server.py
   ├─ mcp_instance.py
   ├─ public_tools.py
   ├─ skill_service.py
   ├─ settings.py
   ├─ workflow_service.py
   ├─ prompts.py
   ├─ resources.py
   ├─ README.md
   ├─ prompts/
   │  ├─ *.txt
   │  └─ profiles/
   │     └─ *.txt
   ├─ resources/
   │  ├─ policies/
   │  │  └─ *.json
   │  ├─ schemas/
   │  │  └─ *.json
   │  └─ templates/
   │     ├─ audit/
   │     ├─ delivery/
   │     ├─ policies/
   │     ├─ specification/
   │     ├─ translation/
   │     └─ profiles.json
   ├─ tools/
   │  ├─ __init__.py
   │  ├─ audit_renderer.py
   │  ├─ baseline_renderer.py
   │  ├─ draft_validator.py
   │  ├─ render_specification.py
   │  ├─ requirement_validator.py
   │  ├─ specification_renderer.py
   │  └─ README.md
   ├─ tests/
   │  ├─ __init__.py
   │  └─ test_public_workflows.py
   └─ docs/
      ├─ contract-baseline.json
      ├─ IO_BOUNDARY.md
      ├─ SERVER_AUDIT.md
      ├─ WORKFLOW.md
      └─ examples/
         └─ minimal_workflow_client.py
```

## Runtime entry chains

```text
run.bat
> .venv/Scripts/python.exe -m server.fastmcp_service
> server/fastmcp_service/__main__.py
> server/fastmcp_service/server.py:main()
> mcp.run()
```

```text
fastmcp.json
> server/entrypoint.py:mcp
> server/fastmcp_service/server.py:mcp
> server/fastmcp_service/mcp_instance.py:mcp
```

```text
compose.yaml
> Dockerfile
> python -m server.fastmcp_service
> server/fastmcp_service/__main__.py
> server/fastmcp_service/server.py:main()
```

## MCP registration links

```text
server.py
> mcp_instance.py
> public_tools.py
```

```text
public_tools.py
> generate_requirements
> generate_architecture
> run_audit
> generate_skill
> workflow_service.py
> skill_service.py
```

## Internal workflow links

```text
workflow_service.py
> prompts.py
> tools/requirement_validator.py
> tools/draft_validator.py
> tools/baseline_renderer.py
> tools/audit_renderer.py
> resources/policies/**
> resources/templates/**
> PXDCA_ARTIFACT_ROOT
> PXDCA_STATE_ROOT
```

```text
prompts.py
> prompts/*.txt
> prompts/profiles/*.txt
> resources/policies/profile-policy.json
> resources/templates/profiles.json
```

```text
tools/requirement_validator.py
> resources/policies/profile-policy.json
```

```text
tools/baseline_renderer.py
> resources/templates/delivery/**
```

```text
tools/audit_renderer.py
> resources/templates/audit/iso-aligned-audit.md
```

## Workflow chains

```text
generate_requirements(q0)
> discovery Prompt
> MCP Sampling
> consultant plan validator
> PXDCA_STATE_ROOT/<session_id>.json
> Q1..Qn
```

```text
generate_requirements(session_id, answer)
> persisted requirement state
> answer-review Prompt
> MCP Sampling
> state validator
> atomic state save
> next question | requirement renderer
```

```text
generate_architecture(session_id)
> completed requirement payload
> technical-alignment Prompt
> MCP Sampling
> draft validator
> planning renderer
```

```text
run_audit(session_id)
> requirement payload + architecture payload
> audit Prompt
> MCP Sampling
> audit validator
> audit renderer
```

```text
generate_skill(mode, customization, output_dir)
> tools/SKILL.md
> template: canonical copy
> optimized: optional MCP Sampling addition
> data/artifacts/pxdca-pdca/SKILL.md by default
> Tool-level output_dir is accepted only when external configuration enables overrides
```

## Storage links

```text
PXDCA_ARTIFACT_ROOT
> data/artifacts/<session_id>/requirements.json
> data/artifacts/<session_id>/requirement-spec.md
> data/artifacts/<session_id>/architecture.json
> data/artifacts/<session_id>/architecture.md
> data/artifacts/<session_id>/audit.json
> data/artifacts/<session_id>/audit.md
> data/artifacts/pxdca-pdca/SKILL.md
```

```text
PXDCA_STATE_ROOT
> data/state/<session_id>.json
```

## Configuration links

```text
install.bat > requirements.txt > .venv/
run.bat > .env + install.bat
fastmcp.json > requirements.txt
Dockerfile > requirements.txt + server/ + tools/SKILL.md
.env > run.bat + compose.yaml
compose.yaml > Dockerfile + config/pxdca.toml + Docker named volumes
.dockerignore > Docker build context
.gcloudignore > gcloud upload context
.gitignore > Git working tree
```
