# AGENTS.md

## Purpose
- This package is a guarded Excel automation workspace for `excel-vba` and its high-risk companion workflows.
- Treat existing `.xlsm` mutation, VBA reinjection, COM automation, and Python/VBA coexistence as contract-sensitive workbook surgery.
- Prefer the smallest safe change and preserve user workbook state over speed.

## Scope
- These rules apply to the `excel_vba/` package root and its descendants unless a deeper `AGENTS.md` or `AGENTS.override.md` says otherwise.

## High-Risk Excel Contract Surface
- existing `.xlsm`
- Python + VBA mixed mutation
- COM automation or VBA reinjection
- workbook-qualified `Application.Run`
- non-ASCII path, filename, sheet name, module name, caption, or button text
- button, shape, `OnAction`, worksheet or workbook event handler
- named range, `ListObject`, table name, or formula-bearing contract surface
- live workbook state or possible unsaved changes
- patch-in-place on an already open workbook

## Mandatory execution posture
- Default to patch-in-place.
- Do not replace workbook structure unless the user explicitly asks for it and the collision review passes.
- Do not force-close a live workbook.
- Do not discard unsaved user edits.
- If workbook state, lock state, or unsaved state is unclear, treat the run as `WARN` or `BLOCKED`.
- Do not treat file creation, save success, or reopen success as completion by themselves.
- Use single-writer execution for same-workbook writes.

## Mandatory validation gate
Only claim completion for high-risk workbook work after all applicable checks pass:
1. workbook open
2. patch or reinjection result
3. compile if VBA changed
4. references if VBA changed
5. named range, table, control, and event binding checks
6. save
7. close
8. reopen
9. workbook-qualified `Application.Run`
10. output integrity
11. no hidden blocker remains

## Truthfulness rule
Do not claim success when any of these remain unverified:
- compile
- references
- reopen
- `Application.Run`
- output integrity
- preservation of unsaved edits

## Heartbeat policy
- Use [heartbeat.md](./heartbeat.md) for COM automation, VBA reinjection, `.xlsm` patching, Python/Excel bridge work, non-ASCII path or caption handling, live workbook runs, unsaved-change risk, or explicit subagent workflows.
- Valid states are `HEARTBEAT_OK`, `HEARTBEAT_WARN`, `HEARTBEAT_BLOCKED`, and `HEARTBEAT_DONE`.

## Parallel rule
- Parallel work is allowed for read-only analysis, collision review, validation planning, and documentation or evidence gathering.
- Parallel writes to the same workbook, VBA project, worksheet event code, named range surface, or control surface are not allowed.

## Skill routing
- Use `excel-vba` for general VBA-first Excel automation.
- Use `excel-xlsm-contract-ops` for existing `.xlsm`, reinjection, `Application.Run`, COM automation, Python/VBA coexistence, non-ASCII path or caption, or live-workbook risk.

## Completion rule
Completion requires all of the following when applicable:
- workbook state safely handled
- no unsaved user work discarded
- reinjection verified
- compile passed
- references passed
- bindings survived
- save-close-reopen passed
- workbook-qualified `Application.Run` passed
- `Result`, `Validation_Errors`, and `LOG` integrity checked
- no hidden blocker remains
