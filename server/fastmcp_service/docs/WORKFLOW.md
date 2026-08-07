# LogicMCP workflow

## Public MCP surface

LogicMCP registers exactly three MCP Tools:

- `generate_requirements`
- `generate_architecture`
- `run_audit`

No MCP Prompts or Resources are registered. Prompt templates, policies, schemas,
validators, state transitions, and renderers are private Server implementation.

## Requirements

```text
q0
> private discovery prompt
> Client LLM Sampling
> consultant-plan validation
> persist Q1..Qn and active question

session_id + answer
> load persisted state
> private answer-review prompt
> Client LLM Sampling
> state-transition validation
> persist the accepted state
> next question or final requirement rendering
```

Calling `generate_requirements` with only `session_id` reads the persisted state
and returns the current question. The MCP connection is not the workflow state.

## Architecture

```text
session_id
> load completed requirement payload
> private technical-alignment prompt
> Client LLM Sampling
> technical-alignment validation
> architecture rendering
> persist payload and artifacts
```

## Audit

```text
session_id
> load completed requirement and architecture payloads
> private audit prompt
> Client LLM Sampling
> audit validation
> audit rendering
> persist payload and artifacts
```

## Failure and resume rule

Only validated state is persisted. The state is saved before a completed
interview advances into document generation. A retry with the same `session_id`
therefore resumes from the last committed phase without repeating accepted
answers. Completed architecture and audit calls are idempotent and return their
existing artifacts.
