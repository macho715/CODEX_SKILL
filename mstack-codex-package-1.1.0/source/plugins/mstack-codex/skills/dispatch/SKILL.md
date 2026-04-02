---
name: mstack-dispatch
description: >
  Task routing and ownership skill for Codex. Use when the main question is how
  to execute safely and efficiently: choose direct work, subagents, or parallel
  teams, define ownership, and plan validation for multi-file or cross-module
  tasks; triggers include delegation, parallelization, ownership split, and
  "작업 분배". Prefer `mstack-pipeline` for one-shot end-to-end execution,
  `mstack-plan` for design-only work, and `mstack-review` for code-review-only
  work.
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

- Count likely changed files.
- Identify whether the work crosses modules.
- Check for API contract changes.
- Check whether the task can be isolated cleanly.

### 2. Choose a mode

- Use direct execution for 1 to 2 files with low coupling.
- Use subagents for 3 to 4 files when the work is separable.
- Use parallel team execution for 5+ files, cross-module work, or API changes.
- Escalate to a lead-led split whenever shared code or coordination risk is high.

### 3. Produce an execution plan

- Name the owner for each file or module.
- State the order of work.
- Call out shared-module risks and review points.
- Define the validation commands before implementation starts.

### 4. Keep the split concrete

- Avoid vague role names.
- Avoid assigning overlapping ownership.
- Give each worker a bounded directory or file list.
- Keep the lead responsible for coordination, review, and final merge decisions.

## Pipeline-Coordinator Routing

- Use `pipeline-coordinator` when the task still has an unresolved
  implementation or architecture decision that should be settled before coding.
- Route to `pipeline-coordinator` only when at least one of these is true:
  `3+ options`, explicit trade-off scoring, irreversible design choice, or the
  user explicitly asks for a fixed multi-agent topology.
- When selected, define this ownership split exactly:
  `pipeline-coordinator` final merge, `orchestrate-analysis` analysis artifact,
  `scenario-scorer` scoring artifact, `analysis-verifier` verification artifact.
- Do not route simple direct work, review-only work, or QA-only work through
  `pipeline-coordinator`.

## Output

Return a compact recommendation with:

- chosen mode
- file count estimate
- coupling or API risk
- ownership split
- validation steps
- rollback risk
