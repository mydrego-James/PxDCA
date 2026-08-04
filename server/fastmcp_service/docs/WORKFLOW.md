# LogicMCP Python Workflow

The optional Python Factory is the explicit workflow controller. FastMCP exposes Prompts, Resources, and Tools; it does not import the Factory, an LLM provider, or an Agent Skill runtime.

## Responsibility boundary

- Python selects the stage, retrieves an MCP Prompt, sends Prompt plus input to the configured LLM, receives JSON, calls deterministic MCP Tools, persists approved State, and returns results.
- Prompts define the LLM role, semantic boundary, and JSON output contract for one atomic model task.
- Resources provide Schemas, Policies, Profiles, and Templates.
- Tools validate JSON and State transitions, persist approved data, and render artifacts.
- The LLM performs natural-language interpretation only. It does not own workflow sequencing or deterministic approval.

## Requirement workflow

### 1. Topic discovery

1. Python calls `get_available_templates`.
2. Python gets `discovery_prompt` and sends Q0 plus the authorized depth profile to the LLM.
3. The LLM returns one complete `Q1..Qn` Consultant Plan draft.
4. Python may run `consultant_plan_review` when the selected release policy requires a second LLM review.
5. Python calls `validate_consultant_plan` or `validate_consultant_plan_review` and stores only the approved State.

### 2. Answer review loop

1. Python keeps the complete Requirement State and the untouched `user_message` separate.
2. Python gets `requirement_interview` using the active question's capability profile.
3. The LLM compares the message with every existing Q item and returns a bounded Patch.
4. Python calls `validate_consultant_answer_review` with the same untouched message and State.
5. Python stores only the approved new State and repeats until convergence.

Python must not create Q ids, parse Qn references, resolve option keys, or decide which question the message answers.

## Draft document workflow

1. `batch_audit_draft` → LLM → `validate_batch_audit_draft` → `render_requirement_baseline`.
2. `technical_alignment_draft` → LLM → `validate_technical_alignment_draft` → `render_planning_baseline`.
3. `iso_audit_draft` → LLM → `validate_audit_draft` → `render_iso_aligned_audit` and `render_enterprise_baseline`.

`system_design_draft` and `pm_contract_draft` are registered Prompt contracts for future stages. Their deterministic Validators and Renderers are not implemented; Python must fail closed and must not claim either stage is complete.

## Runtime call rule

Retrieving a Prompt or Resource and calling a deterministic Tool does not itself call an LLM. Every LLM call must be explicit in Python, logged with its stage, and bounded by the selected workflow policy.
