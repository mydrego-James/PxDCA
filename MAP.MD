# LogicMCP Server — Project Map

## Root tree

```text
LogicMCP_Server/
├─ server/
│  ├─ __init__.py
│  ├─ entrypoint.py
│  └─ fastmcp_service/
├─ tools/
│  ├─ README.md
│  └─ PLAN.md
├─ logs/
│  └─ README.md
├─ output/
│  └─ README.md
├─ .dockerignore
├─ .env.example
├─ .gcloudignore
├─ .gitattributes
├─ .gitignore
├─ compose.yaml
├─ docker.md
├─ Dockerfile
├─ fastmcp.json
├─ install.bat
├─ MAP.MD
├─ README.md
├─ requirements.txt
└─ run.bat
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
   ├─ prompts.py
   ├─ resources.py
   ├─ README.md
   │
   ├─ prompts/
   │  ├─ batch_audit_draft.txt
   │  ├─ consultant_plan_review.txt
   │  ├─ consultant_reconciliation.txt
   │  ├─ discovery.txt
   │  ├─ iso_audit_draft.txt
   │  ├─ pm_contract_draft.txt
   │  ├─ requirement_interview.txt
   │  ├─ system_design_draft.txt
   │  ├─ technical_alignment_draft.txt
   │  └─ profiles/
   │     └─ *.txt
   │
   ├─ resources/
   │  ├─ policies/
   │  │  ├─ domain-policy.json
   │  │  └─ profile-policy.json
   │  ├─ schemas/
   │  │  └─ *.json
   │  └─ templates/
   │     ├─ audit/
   │     ├─ delivery/
   │     ├─ policies/
   │     ├─ specification/
   │     │  ├─ consultant/
   │     │  ├─ professional/
   │     │  └─ simple/
   │     ├─ translation/
   │     └─ profiles.json
   │
   ├─ tools/
   │  ├─ __init__.py
   │  ├─ audit_renderer.py
   │  ├─ baseline_renderer.py
   │  ├─ draft_validator.py
   │  ├─ render_specification.py
   │  ├─ requirement_validator.py
   │  ├─ specification_renderer.py
   │  └─ README.md
   │
   └─ docs/
      ├─ contract-baseline.json
      ├─ IO_BOUNDARY.md
      ├─ SERVER_AUDIT.md
      ├─ WORKFLOW.md
      └─ examples/
         └─ minimal_workflow_client.py
```

## Entry chains

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

## Module links

```text
server.py
> mcp_instance.py
> prompts.py
> resources.py
> tools/__init__.py
```

```text
prompts.py
> prompts/*.txt
> prompts/profiles/*.txt
> resources/policies/profile-policy.json
> resources/templates/profiles.json
```

```text
resources.py
> resources/policies/*.json
> resources/schemas/*.json
```

```text
tools/__init__.py
> tools/requirement_validator.py
> tools/draft_validator.py
> tools/specification_renderer.py
> tools/audit_renderer.py
> tools/baseline_renderer.py
> resources/templates/profiles.json
```

```text
tools/specification_renderer.py
> tools/render_specification.py
> resources/templates/specification/**
```

```text
tools/requirement_validator.py
> resources/policies/profile-policy.json
```

```text
tools/render_specification.py
> resources/schemas/specification-schema.json
> resources/templates/specification/**
```

```text
tools/baseline_renderer.py
> resources/templates/delivery/**
```

```text
tools/audit_renderer.py
> resources/templates/audit/iso-aligned-audit.md
```

```text
tools/__init__.py
> output/
```

```text
mcp_instance.py
> logs/fastmcp/
> output/
```

## Configuration links

```text
install.bat > requirements.txt > .venv/
run.bat > .env + install.bat
fastmcp.json > requirements.txt
Dockerfile > requirements.txt + server/
.env > run.bat + compose.yaml
compose.yaml > Dockerfile + logs/ + output/
.dockerignore > Docker build context
.gcloudignore > gcloud upload context
.gitignore > Git working tree
```
