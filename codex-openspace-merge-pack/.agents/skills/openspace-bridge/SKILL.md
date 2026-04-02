---
name: openspace-bridge
description: Decide whether the current task should stay inside existing Codex skills or escalate through OpenSpace host skills. Use when the task is unfamiliar, tool-heavy, likely to benefit from reusable skills, or requires delegation after failure.
---

# OpenSpace Bridge

## Purpose
Use the current repo skills first when they are sufficient.
Use OpenSpace only when reuse, delegation, repair, or complex execution is clearly beneficial.

## Inputs
- User task
- Current repo skills available in `.agents/skills`
- OpenSpace host skills:
  - `skill-discovery`
  - `delegate-task`

## Routing logic

### 1. Discovery first
For unfamiliar, complex, or repetitive tasks:
- run `skill-discovery`
- search for a local or imported skill match

### 2. Stay local when possible
Keep the task inside existing Codex skills when:
- a repo skill already covers the workflow,
- the task is mostly reasoning, planning, review, writing, or scoring,
- no additional tool/system reach is needed.

### 3. Escalate to OpenSpace when needed
Use `delegate-task` / `execute_task` when any of these are true:
- there is a clear capability gap,
- the task needs broader tool orchestration,
- the task is multi-step and benefits from OpenSpace skill search/evolution,
- the local approach already failed once.

### 4. Post-delegation
After any OpenSpace delegation:
- summarize what was delegated,
- record any evolved skills,
- decide whether upload is appropriate,
- send the result to `analysis-verifier`.

## Hard rules
- Do not bypass local repo skills if they already solve the task well.
- Do not delegate trivial tasks just because OpenSpace is available.
- Do not upload evolved skills unless the user or project policy allows it.

## Output contract
Return one of:
- `LOCAL_ONLY`
- `LOCAL_WITH_SKILL_IMPORT`
- `DELEGATE_TO_OPENSPACE`

and include:
- reason,
- selected skill(s),
- expected next step.
