# VBA-Python Conflict Checklist

Use this file whenever Python-generated workbook output may coexist with VBA.

## Mandatory review items
- file format collision
- sheet name collision
- standard output sheet or fixed VBA reference sheet collision
- header structure collision
- start row, header row, and start cell collision
- `ListObject` or table name collision
- named range collision
- formula placement collision
- formatting or merged-cell collision
- hidden sheet or protected sheet collision
- worksheet event handler collision
- macro preservation risk
- overwrite risk on an existing `.xlsm`
- auto-filter or table-range collision with VBA array-processing expectations
- non-ASCII path or filename collision
- open-workbook safety risk

## Required output block
When Python is included, add this block to the answer:

`VBA-Python Collision Review`

- `File format collision:`
- `Sheet name collision:`
- `Standard output/reference sheet collision (Result, Validation_Errors, LOG, fixed VBA sheets):`
- `Header structure collision:`
- `Start row/header row/start cell collision:`
- `ListObject collision:`
- `Named range collision:`
- `Formula placement collision:`
- `Formatting or merged-cell collision:`
- `Hidden sheet or protected sheet collision:`
- `Worksheet event handler collision:`
- `Macro preservation risk:`
- `Overwrite risk on an existing .xlsm:`
- `Auto-filter or table-range collision:`
- `Non-ASCII path or filename collision:`
- `Open-workbook safety risk:`
- `Result:`

## Default mitigation patterns
- Keep the macro-enabled source workbook and Python-generated workbook separate unless the user explicitly requests in-place editing.
- Prefer patching existing workbook structures in place when VBA state must survive, and do not delete or recreate tables, named ranges, controls, or event handlers unless the user explicitly requests it and the collision review passes.
- If names would collide, use a Python prefix such as `Py_`.
- If VBA expects a fixed sheet such as `InputData`, do not let Python rename or repurpose it without calling that out.
- Prefer a new `.xlsx` report when Python output does not need to carry VBA modules.

## Conditional hold or safe-alternative cases
- direct overwrite of an active production `.xlsm`
- save-format changes that would almost certainly strip macros
- structural changes to protected or signed workbooks
- delete or reset operations that could remove user data
- an open workbook with unsaved user edits

When one of these applies, prefer a safe alternative structure before approving in-place modification.
