# Decision Tree

## 1. Is the workbook live?

- If yes:
  - Is the unsaved state known?
    - If not, report `BLOCKED` or at least `WARN`.
    - If yes, confirm whether live patching is allowed.
- If no, continue.

## 2. Is the path, caption, or sheet name non-ASCII?

- If yes, raise Unicode risk and require target-path validation.
- If no, use normal path rules.

## 3. Is VBA reinjection required?

- If yes, compile, references, save-close-reopen, and workbook-qualified `Application.Run` are mandatory.
- If no, use the standard workbook validation path.

## 4. Do Python and VBA touch the same workbook surface?

- If yes, collision review is mandatory.
- If no, use standard workbook validation.

## 5. Are touched surfaces contract-sensitive?

Treat these as contract-sensitive:
- button
- shape
- `OnAction`
- worksheet or workbook event
- named range
- `ListObject`
- formula-bearing placement
- macro entrypoint
- `Result`, `Validation_Errors`, `LOG`
- visible-session behavior

## 6. Choose write posture

- Use read-only analysis for workbook state review, collision review, or Unicode risk review.
- Use serial single-writer for actual workbook patching.
- Use blocked when live workbook state is unsafe or required inputs are missing.
