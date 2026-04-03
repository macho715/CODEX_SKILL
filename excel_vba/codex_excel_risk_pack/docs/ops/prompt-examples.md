# Prompt Examples

## 1. Guarded serial write

```text
Use explicit subagent workflows.
Have manager create the plan.
Have guardrail inspect live workbook state, unsaved risk, Unicode risk, reinjection risk, and collision surfaces.
If guardrail does not return BLOCKED, have implementer apply a single-writer patch in place.
Then have verifier validate compile, references, save-close-reopen, workbook-qualified Application.Run, and output integrity.
Update heartbeat.md at each major stage.
```

## 2. Read-only preflight only

```text
Do not edit anything yet.
Use guardrail to inspect this existing .xlsm for live workbook risk, Unicode path risk, Application.Run risk, and Python/VBA contract collisions.
Return a write posture decision and the minimum validation gates before implementation.
Update heartbeat.md with WARN or BLOCKED if needed.
```

## 3. Python + VBA coexistence

```text
Use the excel-xlsm-contract-ops skill.
Treat this as a high-risk Excel contract surface.
Check Result, Validation_Errors, LOG, named ranges, ListObject names, formula positions, event handlers, and macro preservation before any patch.
Use single-writer implementation and verifier-led runtime validation.
```

## 4. Live workbook with possible unsaved changes

```text
This workbook may already be open and may contain unsaved edits.
Do not force close Excel.
Do not overwrite blindly.
Have guardrail determine whether the run is BLOCKED, and if blocked, return exactly three input requirements.
```

## 5. Unicode / non-ASCII path

```text
The target workbook path, sheet names, and button captions include non-ASCII characters.
Do not assume ASCII path validation is enough.
Require actual target-path validation for save, close, reopen, and workbook-qualified Application.Run.
```
