---
name: mstack-dispatch
description: >
  Task routing and ownership skill for Codex. Use when the main question is how
  to execute safely and efficiently: choose direct work, subagents, or parallel
  teams, define ownership, and plan validation for multi-file or cross-module
  tasks, and when the user is asking to proceed rather than just compare
  options, actually execute the chosen mode instead of stopping at a routing
  summary; triggers include delegation, parallelization, ownership split,
  "작업 분배", and requests to continue a project from the current state.
  Prefer `mstack-pipeline` for one-shot end-to-end execution, `mstack-plan` for
  design-only work, and `mstack-review` for code-review-only work.
---

# Task Routing

## Use This Skill When

- the main decision is direct execution vs subagents vs parallel teams
- the task needs a concrete ownership split, coordination plan, or validation
  routing
- the user asks how to divide or route multi-file or cross-module work

## Prefer Another Skill When

- the user wants one-shot end-to-end SDLC execution: use `mstack-pipeline`
- the user wants only a design or implementation plan: use `mstack-plan`
- the user wants only code or diff review: use `mstack-review`

```
Task request
    |
    v
analyze scope -> choose mode -> assign owners -> define validation
```

## Routing Rules

### 1. Measure scope

- Reconstruct the current state before choosing a mode.
- Inspect the repo or workspace state, existing plans, review notes, open test
  failures, and any staged or modified files.
- Treat the approved planned scope as authoritative for the current run.
- Count planned file targets from the user request, `plan.md`, review notes, or
  explicit module list before counting the smallest possible fix.
- Count likely changed files.
- Identify whether the work crosses modules.
- Check for API contract changes.
- Check whether the task can be isolated cleanly.
- Do not downgrade a 5+ file or cross-module request to direct execution only
  because a local fix looks smaller after reproducing the failure.
- Only narrow the approved scope when the user explicitly changes scope or when
  a new checkpoint report lists the original targets as reviewed and no longer
  required.

### 2. Choose a mode

- Use direct execution for 1 to 2 files with low coupling.
- Use subagents for 3 to 4 files when the work is separable.
- Use parallel team execution for 5+ files, cross-module work, or API changes.
- Escalate to a lead-led split whenever shared code or coordination risk is high.
- Treat `5+ planned files`, `cross-module`, or `API contract change` as
  `parallel required`, not just `parallel recommended`.

### 3. Decide whether to route only or route and execute

- If the user asked only for mode selection, comparison, or a staffing
  recommendation, return a routing summary only.
- If the user asked to continue, execute, delegate, parallelize, fix, finish,
  or invoked `dispatch` mid-project without limiting language, treat the
  request as route-and-execute.
- Do not silently downgrade a route-and-execute request into recommendation
  only.

### 4. Execute the chosen mode when execution was requested

- For direct execution, say that the lead is keeping the work local and proceed
  with the task.
- For subagents, actually start at least one worker with bounded ownership
  instead of only recommending delegation.
- For parallel team execution, actually start 2 or more workers with disjoint
  ownership when tooling allows it.
- Keep the lead responsible for shared modules, coordination, review, and final
  integration.
- If tooling, policy, or coupling blocks delegation for a `parallel required`
  or `subagents required` case, stop and report `blocked`.
- In a `parallel required` or `subagents required` run, do not implement the
  task locally, do not claim completion, and do not treat a transparent
  single-agent fallback as acceptable execution.
- Only downgrade to direct execution after the user explicitly accepts that
  single-agent fallback in the current thread.

### 5. Produce an execution plan

- Name the owner for each file or module.
- State the order of work.
- Call out shared-module risks and review points.
- Define the validation commands before implementation starts.

### 6. Keep the split concrete

- Avoid vague role names.
- Avoid assigning overlapping ownership.
- Give each worker a bounded directory or file list.
- Keep the lead responsible for coordination, review, and final merge decisions.

## Output

Return a compact recommendation with:

- chosen mode
- required mode
- route-only vs route-and-execute
- file count estimate
- coupling or API risk
- current-state evidence used for routing
- planned scope evidence used for routing
- ownership split
- delegation status
- blocked or downgrade reason when required delegation did not happen
- final status
- validation steps
- rollback risk
