---
name: excel-xlsm-contract-ops
description: 기존 .xlsm에서 Python + VBA mixed mutation, COM automation, VBA reinjection, Application.Run, non-ASCII path/caption, live workbook, button/shape/event/named-range/table collision risk가 있는 고위험 Excel 작업을 guarded single-writer workflow로 처리할 때 사용.
---

# Excel XLSM Contract Ops

## When to use

다음 중 하나면 이 Skill을 사용한다.

- existing `.xlsm`
- Python + VBA mixed changes
- COM automation
- VBA reinjection
- workbook-qualified `Application.Run`
- non-ASCII path / filename / sheet name / caption
- button / shape / `OnAction`
- worksheet / workbook event handler
- named range / `ListObject` / table name
- live workbook with possible unsaved changes

## Do not use

다음은 이 Skill이 아닌 일반 작업으로 처리할 수 있다.

- pure formatting with no contract-sensitive surface
- static documentation only
- isolated `.xlsx` read-only analysis
- workbook 외부 일반 코드 리팩터링

## Inputs

- workbook path
- open / lock / unsaved state if known
- target macro entrypoint if any
- touched surfaces
- whether Python changes workbook structure
- whether VBA reinjection is required
- validation success criteria

## Procedure

1. **Risk classify**
   - live workbook
   - Unicode risk
   - reinjection risk
   - collision risk
   - approval risk

2. **Choose execution posture**
   - read-only diagnosis
   - serial single-writer patch
   - blocked pending input

3. **Patch in place**
   - preserve workbook contract
   - avoid structure replacement unless explicitly requested
   - do not discard unsaved user edits

4. **Validate**
   - compile if VBA changed
   - references if VBA changed
   - named range / ListObject / control / event integrity
   - save
   - close
   - reopen
   - workbook-qualified `Application.Run`
   - output integrity

5. **Report**
   - heartbeat update
   - touched surfaces
   - validation result
   - blocker or next action

## Required references

- `references/decision-tree.md`
- `references/output-contract.md`

## Safety

- blind overwrite 금지
- force close 금지
- unsaved user work discard 금지
- same-workbook same-surface parallel write 금지
- file creation or save success만으로 완료 주장 금지
