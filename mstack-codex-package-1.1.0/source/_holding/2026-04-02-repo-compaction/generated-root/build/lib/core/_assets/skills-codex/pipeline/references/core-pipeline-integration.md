# Core Pipeline Integration Design

This note defines how `mstack-pipeline` should align with
`core/pipeline.py`,
`core/pipeline_runner.py`,
and `core/pipeline_recipes.py`
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

## Windows Node Toolchain Note

When the runtime executes `npm`, `npx`, or `node` commands on Windows, treat
the process environment as part of the runtime contract.

- `cmd.exe` can fail once inherited environment strings become excessively long
  or heavily duplicated.
- npm lifecycle scripts prepend local `.bin` directories to `PATH`.
- `@npmcli/run-script` does not automatically add the Node install directory to
  the child `PATH`.

That combination can break otherwise valid Node installs during lifecycle,
lint, test, or typecheck steps. MStack now uses a targeted mitigation for
Node-family subprocesses, but this should be documented as a local safeguard,
not as a complete machine fix.

Operational guidance for users and operators:
- keep `PATH` short and deduplicated on Windows
- make sure `C:\Program Files\nodejs` remains resolvable from `cmd.exe`
- after editing `PATH`, restart the shell or IDE before retrying the pipeline
- verify with:
  `cmd.exe /d /c "where node && where npm && node --version && npm --version"`

Reference sources:
- Microsoft Learn: `cmd.exe` command-line and environment string limitation
- npm Docs: scripts and lifecycle `PATH` behavior
- `@npmcli/run-script`: Windows shell behavior and no `prepend-node-path`

`mstack-pipeline` already documents the same high-level stage chains.

## Boundary Guardrail

`mstack-pipeline` should be treated as the top-level orchestrator only.
If the user is asking for a single design decision, a review-only pass, a
verification-only run, or a simple explanation, the runtime should prefer the
stage-specific skill instead of escalating to the full pipeline.

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
- `requires_parallel_decision`
- `decision_engine`
- `coordinator_input_ready`
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
- `decision engine`
- `coordinator verdict`
- `remaining gaps`
- `retries used`
- `final status`
- `blockers`
- `next action`

## Nested Decision Engine

`pipeline-coordinator` is not a new `core/pipeline.py` stage.
It is a nested decision step that can run after `dispatch` and before
implementation once plan or investigation output provides the required handoff.

## Safe First Implementation

Before full code integration:
- keep `mstack-pipeline` as a skill
- use runtime smoke to lock canonical stage order
- treat `core/pipeline.py` as the execution reference
- treat `core/pipeline_runner.py` and `core/pipeline_recipes.py` as the current
  implement/runtime backend reference
- update the skill whenever the engine changes
