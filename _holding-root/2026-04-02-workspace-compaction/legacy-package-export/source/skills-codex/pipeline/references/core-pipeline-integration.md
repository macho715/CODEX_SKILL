# Core Pipeline Integration Design

This note defines how `mstack-pipeline` should align with
[`core/pipeline.py`](C:/Users/jichu/Downloads/ccat/core/pipeline.py),
[`core/pipeline_runner.py`](C:/Users/jichu/Downloads/ccat/core/pipeline_runner.py),
and [`core/pipeline_recipes.py`](C:/Users/jichu/Downloads/ccat/core/pipeline_recipes.py)
when the skill is wired directly into the code engine.

## Goal

Make the skill and code runtime describe the same stage model so that:
- user-facing skill guidance matches actual engine behavior
- retry semantics are identical in docs and execution
- `dispatch`, `pipeline`, and `qa` do not drift

## Current Alignment

`core/pipeline.py` already defines:
- `PIPELINE_TEMPLATES`
- `AUTO_RETRY_STAGES`
- `MAX_RETRIES`
- `STAGE_TO_SKILL`
- `execute_pipeline()`
- `generate_dispatch_prompt()`

`core/pipeline_runner.py` now provides:
- real `plan`, `review`, `qa`, `ship`, `retro`, `investigate` backends
- recipe-backed `implement` execution
- optional generic implement backend injection

Actual TypeScript toolchain validation is opt-in and should run only when
`RUN_TS_REAL_TOOLCHAIN=1` is set for the dedicated CLI integration test.

`mstack-pipeline` already documents the same high-level stage chains.

## Boundary Guardrail

`mstack-pipeline` should be treated as the top-level orchestrator only.
If the user is asking for a single design decision, a review-only pass, a
verification-only run, or a simple explanation, the runtime should prefer the
stage-specific skill instead of escalating to the full pipeline.

## Required Orchestration Behavior

When the user invokes `mstack-pipeline` in the middle of ongoing work, the
orchestrator should:
- reconstruct state from the current repo, notes, tests, and generated artifacts
- determine the furthest incomplete stage
- resume from that stage instead of restarting from `plan` by default

When `mstack-dispatch` selects `subagents` or `parallel team` and the user has
asked to proceed, the orchestrator should:
- actually launch the delegated work when the environment allows it
- explicitly report any downgrade to direct execution instead of silently
  continuing as a single agent
- treat `5+ planned files`, `cross-module`, or `API-changing` scope as
  `parallel required` unless the user explicitly approves a single-agent
  fallback
- stop with `blocked` or `partial` if required delegation did not happen
- treat approved scope as authoritative for the current run instead of allowing
  a smaller reproduced failure to silently redefine the route

## Known Gap

Today `mstack-pipeline` is prompt-level orchestration only.
It does not call `execute_pipeline()` directly in the skill body, so the
following can drift:
- exact stage order wording
- retry behavior wording
- work-type classification defaults
- stop conditions vs engine stop conditions
- documented summary fields vs `PipelineResult.to_dict()`
- recipe coverage vs actual runtime-backed `implement` behavior
- dispatch recommendation vs actual delegation execution
- mid-project resume behavior vs restart-from-plan behavior
- required parallel execution vs silent direct-execution fallback

## Proposed Direct Connection

### 1. Add an adapter layer

Create a small adapter that maps a natural-language request into:
- `WorkType`
- optional `skip_stages`
- optional checkpoint/approval gate
- execution mode metadata from `mstack-dispatch`

### 2. Use engine state as source of truth

When `mstack-pipeline` is invoked in an automated path:
- classify the request
- call `execute_pipeline(work_type, stage_runner, ...)`
- derive the final user summary from `PipelineResult`

### 3. Keep skill text in sync with code

Whenever these change in `core/pipeline.py`, update `mstack-pipeline`:
- `PIPELINE_TEMPLATES`
- `AUTO_RETRY_STAGES`
- `MAX_RETRIES`
- `STAGE_TO_SKILL`

## Proposed Adapter Contract

Input:
- raw user request
- optional dispatch result
- optional approval/checkpoint preference

Output:
- `work_type`
- `stage_order`
- `execution_mode`
- `approval_gate`
- `pipeline_result`
- `files_changed`
- final summary for the user

## Summary Rules

The final `mstack-pipeline` summary should be generated from `PipelineResult`
and always include:
- `work type`
- `execution mode`
- `stage order`
- `files changed`
- `retries used`
- `final status`
- `blockers`
- `next action`

## Safe First Implementation

Before full code integration:
- keep `mstack-pipeline` as a skill
- use runtime smoke to lock canonical stage order
- treat `core/pipeline.py` as the execution reference
- treat `core/pipeline_runner.py` and `core/pipeline_recipes.py` as the current
  implement/runtime backend reference
- update the skill whenever the engine changes
