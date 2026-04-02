# QA and Operations

Use this file before final output.

## QA sequence
1. 10-row test
2. total and count validation
3. edge-case validation
4. if COM or VBA injection is involved, save, close, reopen, and run the workbook-qualified entry macro
5. validate user-facing controls such as buttons, filters, and conditional formatting when they are part of the deliverable
6. full-run recommendation
7. save and reopen validation
8. if the workbook is already open with user edits, do not force-close it; work on a copy or ask for an explicit override
9. after VBA reinjection, validate compile status, broken references, named ranges, and control bindings

For repeated Windows Excel COM workflows, prefer the bundled script `scripts/build-reopen-smoketest.ps1` instead of rebuilding the same orchestration each turn.

## Edge cases to check
- hidden rows
- text-form numbers
- text-form dates
- duplicate keys
- leading zeros
- blank cells
- whitespace-only cells
- error values
- merged cells
- active filters
- header typos
- missing sheet
- missing file
- non-ASCII path or filename
- VBA module import or injection
- existing worksheet event handlers without marker comments
- workbook-qualified macro name
- open workbook with unsaved changes

## Silent-failure rule
- Do not allow silent failure.
- Record issues in `Validation_Errors` and `LOG`.
- Use visible execution feedback when appropriate, such as `MsgBox` or `Application.StatusBar`.

## Failure handling
- If a draft-stage solution fails, suggest an updated assumption set.
- If a deployment-stage solution fails, present a safer alternative structure.
- If `Application.Run` fails right after VBA injection, first check syntax and encoding, then retry after save, close, and reopen before changing business logic.
- If a worksheet event handler already exists, resolve the collision before reinjecting rather than appending a duplicate handler.

## Operating modes
- `A: VBA manual`
- `B: VBA + Python workbook construction`
- `C: VBA + Python existing-workbook update (explicit request only)`
- `D: shared-folder operation`

Python-only reporting is out of scope.
Python is allowed only when it builds, reshapes, or safely updates Excel sheets or files for the VBA workflow.

## Final objective
- reduce manual work by about 80 percent
- keep the automation reproducible
- keep the workbook maintainable for Excel users
- keep the result auditable through logs and validation outputs
