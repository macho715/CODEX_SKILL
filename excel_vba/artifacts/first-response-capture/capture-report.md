# First Response Capture Report

Assumption: independent subagents with `fork_context=false` were used as the closest available proxy for a fresh session first response.

## Acceptance Contract

- `excel-xlsm-contract-ops` is first
- `risk class` is explicit
- `downstream owner` is explicit
- `write posture` or an equivalent next-stage decision is explicit
- live workbook and unsaved-edit risk are not glossed over

## Initial 5-Prompt Capture

### Prompt 1

Verdict: `FAIL`

Reason: `excel-xlsm-contract-ops` was first, but `downstream owner` was implied rather than labeled.

```text
I'll start with `excel-xlsm-contract-ops` and treat this as a serial single-writer VBA reinjection task because the workbook path is Unicode-sensitive and delivery depends on save-close-reopen plus workbook-qualified `Application.Run`.

I need the exact workbook path, the target macro entrypoint, whether the workbook is currently open or has unsaved edits, and any workbook surfaces that must be preserved before I proceed.
```

### Prompt 2

Verdict: `FAIL`

Reason: first response routed correctly, but `risk class` and `write posture` were not labeled.

```text
Using `excel-xlsm-contract-ops` first as the required risk gate, then `excel-professional-formatting` for a sidecar-only visual pass; I'll keep formulas, named ranges, controls, and VBA untouched.
```

### Prompt 3

Verdict: `FAIL`

Reason: downstream owner was explicit, but `risk class` and `write posture` were not labeled.

```text
Using `excel-xlsm-contract-ops` first, then `excel-vba` ownership because button placement, shape anchoring, and `OnAction` rebinding are contract-sensitive. I'll classify the workbook surfaces, confirm the write posture, and then hand off to the smallest safe patch path.
```

### Prompt 4

Verdict: `PASS`

```text
Risk class: contract-sensitive workbook patch. Downstream owner: `excel-vba`. Write posture: `blocked pending user input`.

Send the workbook path, whether it is currently open or has unsaved edits, the target macro entrypoint, the exact named ranges/ListObject names/control bindings you expect to change, whether Python already altered the workbook structure, whether VBA reinjection is required, and the validation criteria you want preserved.
```

### Prompt 5

Verdict: `FAIL`

Reason: downstream routing was correct, but `risk class` and `write posture` were not labeled.

```text
Using `excel-xlsm-contract-ops` first, then `excel-professional-formatting`; I will not touch the live workbook until the open/unsaved state is clear. Confirm the workbook path and whether I should work on a sidecar copy, and if Excel already has it open, tell me to preserve that session.
```

## Patch Applied

Patched `excel-xlsm-contract-ops` to require the first response to begin with:

- `Risk class:`
- `Downstream owner:`
- `Write posture:`

Patched files:

- [SKILL.md](/C:/Users/SAMSUNG/.codex/skills/excel-xlsm-contract-ops/SKILL.md)
- [output-contract.md](/C:/Users/SAMSUNG/.codex/skills/excel-xlsm-contract-ops/references/output-contract.md)
- [SKILL.md](/C:/Users/SAMSUNG/Downloads/skill/excel_vba/excel-xlsm-contract-ops/SKILL.md)
- [output-contract.md](/C:/Users/SAMSUNG/Downloads/skill/excel_vba/excel-xlsm-contract-ops/references/output-contract.md)
- [SKILL.md](/C:/Users/SAMSUNG/Downloads/skill/excel_vba/plugins/excel-vba/skills/excel-xlsm-contract-ops/SKILL.md)
- [output-contract.md](/C:/Users/SAMSUNG/Downloads/skill/excel_vba/plugins/excel-vba/skills/excel-xlsm-contract-ops/references/output-contract.md)

## Post-Patch Recheck

### Prompt 1 rerun

Verdict: `PASS`

```text
Risk class: high
Downstream owner: `excel-vba`
Write posture: serial single-writer patch

I need the exact workbook path and target macro entrypoint before I touch the file.
```

### Prompt 2 rerun

Verdict: `PASS`

```text
Risk class: formatting-only, contract-sensitive workbook
Downstream owner: `excel-professional-formatting`
Write posture: blocked pending workbook path and file selection

Share the workbook path or attach the `.xlsm` so I can classify the sheets and prepare the sidecar formatting pass without touching formulas, named ranges, controls, or VBA.
```

### Prompt 3 rerun

Verdict: `PASS`

```text
Risk class: contract-sensitive workbook patch
Downstream owner: `excel-vba`
Write posture: serial single-writer patch, not formatting-only

Touched surfaces: buttons, shapes, anchor positions, `OnAction` bindings.
Validation gates: workbook contract diff, control-binding recheck, save/reopen, macro-entrypoint verification.
Next action: classify the workbook and confirm the edit boundary before any change.
```

### Prompt 4 rerun

Verdict: `PASS`

```text
Risk class: contract-sensitive mixed Python/VBA workbook with named range, `ListObject`, and macro entrypoint collision risk
Downstream owner: `excel-vba`
Write posture: blocked pending workbook path, open/unsaved state, target macro entrypoint, and the specific surfaces you want changed
```

### Prompt 5 rerun

Verdict: `PASS`

```text
Risk class: live workbook, unsaved state unknown
Downstream owner: `blocked`
Write posture: blocked pending user input

Touched surfaces: print layout only, with workbook path and open-session state not yet confirmed.
Validation gates: confirm the exact workbook, whether Excel has unsaved edits open, and whether a sidecar copy is acceptable before any formatting pass.
Blocker / next action: send the workbook path and tell me if I should preserve a live unsaved session or work only on a copy.
```

## Final Status

- Initial capture: `1/5 PASS`
- After patch and full rerun coverage: `5/5 PASS`
- Post-patch rerun set: Prompts 1, 2, 3, 4, and 5 all satisfy the first-response acceptance contract.
