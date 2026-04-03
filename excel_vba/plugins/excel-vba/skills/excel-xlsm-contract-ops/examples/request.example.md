# Example Requests

## Scenario 1: Existing `.xlsm` reinjection

Patch an existing `.xlsm` that may already be open, reinject VBA, preserve controls and named ranges, and do not call the work done until save-close-reopen plus workbook-qualified `Application.Run` passes on the actual target path.

## Scenario 2: Formatting-only release behind the risk gate

This looks like a print-layout and readability cleanup only, but the workbook is macro-enabled. Run the contract risk gate first, state the risk class, then release the task to `excel-professional-formatting` only if no contract-sensitive surfaces need intervention.

## Scenario 3: Live workbook with unsaved-edit risk

The user wants the workbook to print cleanly, but the file may already be open in Excel with unsaved edits. Classify live-workbook risk first, do not gloss over unsaved changes, and state whether the next step is `excel-professional-formatting` or `blocked`.
