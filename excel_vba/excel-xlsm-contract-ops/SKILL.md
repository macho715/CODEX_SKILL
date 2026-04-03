---
name: excel-xlsm-contract-ops
description: Guard high-risk Excel contract work involving existing `.xlsm` files, Python and VBA mixed mutation, COM automation, VBA reinjection, workbook-qualified `Application.Run`, non-ASCII paths or captions, and live workbook state with a serial single-writer workflow. Use this as the mandatory first risk-gate stage whenever `excel-vba` or `excel-professional-formatting` is used on a workbook.
---

# Excel XLSM Contract Ops

## trigger

Use this skill when the request touches an existing `.xlsm`, Python and VBA change the same workbook, COM automation or VBA reinjection is required, workbook-qualified `Application.Run` matters, non-ASCII workbook paths or captions are involved, or controls, events, named ranges, `ListObject` names, and other contract-sensitive workbook surfaces may collide.

## non-trigger

Do not use this skill for static documentation work, isolated read-only `.xlsx` analysis, or routine workbook generation that does not touch contract-sensitive workbook state. Pure formatting passes are still routed here first when the workbook will continue into `excel-professional-formatting`, because this skill owns the initial risk gate and downstream-owner decision.

## steps

1. Start every `excel-vba` or `excel-professional-formatting` workbook run here, before any workbook edit or handoff.
2. Read [references/decision-tree.md](references/decision-tree.md) first to classify live workbook, Unicode, reinjection, and collision risk.
3. Gather the workbook path, open or unsaved state if known, target macro entrypoint, touched surfaces, whether Python changes workbook structure, whether VBA reinjection is required, and the validation success criteria.
4. Choose a write posture: formatting-only release, read-only diagnosis, serial single-writer patch, or blocked pending user input.
5. Patch in place by default, preserve workbook contracts, and do not discard unsaved user edits.
6. Keep the chosen risk class visible through any later `excel-vba` or `excel-professional-formatting` handoff, and reclaim ownership if new contract-sensitive surfaces appear.
7. In the first response, start with explicit labels for `Risk class:`, `Downstream owner:`, and `Write posture:` before any explanatory prose.
8. Validate compile and references when VBA changed, then validate named ranges, `ListObject` names, control bindings, event bindings, save, close, reopen, workbook-qualified `Application.Run`, and output integrity.
9. Report with the fixed output order in [references/output-contract.md](references/output-contract.md) and update `heartbeat.md` when runtime verification is still active.

## verification

Pass only when all applicable checks are explicit:

- risk class is stated
- the downstream owner is stated as `excel-vba`, `excel-professional-formatting`, or `blocked`
- touched surfaces are listed
- write posture is stated
- validation gates are listed
- heartbeat recommendation is stated
- blocker or next action is stated
- compile and references are verified if VBA changed
- save, close, reopen, and workbook-qualified `Application.Run` are verified when applicable
- output integrity is verified
- unsaved user edits are preserved

## safety

- Never blind overwrite a live workbook.
- Never force close Excel.
- Never discard unsaved user edits.
- Never allow same-workbook same-surface parallel write.
- Never claim done because file creation or save succeeded.
