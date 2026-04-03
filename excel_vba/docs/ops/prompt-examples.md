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
Use guardrail to inspect this existing .xlsm for live workbook risk, Unicode path risk, Application.Run risk, and Python and VBA contract collisions.
Return a write posture decision and the minimum validation gates before implementation.
Update heartbeat.md with WARN or BLOCKED if needed.
```

## 3. Python and VBA coexistence

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

## 5. Unicode or non-ASCII path

```text
The target workbook path, sheet names, and button captions include non-ASCII characters.
Do not assume ASCII path validation is enough.
Require actual target-path validation for save, close, reopen, and workbook-qualified Application.Run.
```

## 6. First-response regression checklist

Use this checklist when validating the first response shape for the `excel-xlsm-contract-ops -> excel-vba / excel-professional-formatting` pipeline.

Acceptance contract:

- `excel-xlsm-contract-ops` appears first
- `Risk class:` is explicit
- `Downstream owner:` is explicit
- `Write posture:` is explicit
- live-workbook and unsaved-edit risk are not glossed over

Regression prompts:

### Prompt 1: High-risk reinjection

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)

Existing `.xlsm`. VBA reinjection required. Workbook path contains Korean characters. Delivery is not complete until save-close-reopen and workbook-qualified `Application.Run` pass on the actual target path. Return only the first response you would give before implementation details.
```

Expected:
- downstream owner `excel-vba`
- serial single-writer or blocked posture

### Prompt 2: Formatting-only release

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-professional-formatting](C:\Users\SAMSUNG\.codex\skills\excel-professional-formatting\SKILL.md)

This is an existing macro-enabled workbook. The request is only to improve readability, print layout, and professional formatting. Do not touch formulas, named ranges, controls, or VBA. Return only the first response you would give before implementation details.
```

Expected:
- downstream owner `excel-professional-formatting`
- formatting-only or path-selection gate before sidecar work

### Prompt 3: Formatting escalation to VBA

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)
[$excel-professional-formatting](C:\Users\SAMSUNG\.codex\skills\excel-professional-formatting\SKILL.md)

The workbook was visually cleaned already, but now the request includes button placement fixes, shape drift, and `OnAction` rebinding. Return only the first response you would give before implementation details.
```

Expected:
- downstream owner `excel-vba`
- not formatting-only

### Prompt 4: Python plus VBA collision risk

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)

Python generated part of this workbook, and now VBA changes will touch named ranges, `ListObject` names, and macro entrypoints in the same file. Return only the first response you would give before implementation details.
```

Expected:
- downstream owner `excel-vba`
- blocked or serial single-writer posture until surfaces are confirmed

### Prompt 5: Live workbook with unsaved risk

```text
[$excel-xlsm-contract-ops](C:\Users\SAMSUNG\.codex\skills\excel-xlsm-contract-ops\SKILL.md)
[$excel-professional-formatting](C:\Users\SAMSUNG\.codex\skills\excel-professional-formatting\SKILL.md)
[$excel-vba](C:\Users\SAMSUNG\.codex\skills\excel-vba\SKILL.md)

The user wants the print layout polished, but the workbook may already be open in Excel and the unsaved state is unclear. Return only the first response you would give before implementation details.
```

Expected:
- downstream owner `blocked` unless live-state handling is explicit
- no glossing over unsaved-edit preservation

Reference evidence:
- [capture-report.md](/C:/Users/SAMSUNG/Downloads/skill/excel_vba/artifacts/first-response-capture/capture-report.md)
- [prompt-set.md](/C:/Users/SAMSUNG/Downloads/skill/excel_vba/artifacts/first-response-capture/prompt-set.md)
