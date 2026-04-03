# Example Requests

## Scenario 1: Idea-stage macro design

Build a starter `.xlsm` workflow for monthly invoice validation. I only know that users will paste rows into one input sheet and click a button to generate `Result`, `Validation_Errors`, and `LOG`.

## Scenario 2: Formatting-to-VBA escalation

The workbook was visually cleaned up already, but now the request also touches button placement, shape drift, and `OnAction` rebinding. Keep styling work separate and take ownership of the contract-sensitive parts in `excel-vba`.

## Scenario 3: Python plus VBA workbook build

Generate the workbook shell with Python, then wire the shipping workflow in VBA. The workbook path may contain non-ASCII characters, and delivery is not complete until save-close-reopen plus workbook-qualified macro smoke validation passes.

## Scenario 4: Formatting-only release after contract gate

This is still an existing macro-enabled workbook. Run the `excel-xlsm-contract-ops` risk gate first, and if the request stays formatting-only, hand it to `excel-professional-formatting` for a sidecar formatting pass without touching formulas, named ranges, controls, or VBA.

## Scenario 5: Live workbook with unsaved edits

The user wants the print layout polished, but the workbook may already be open in Excel and the unsaved state is unclear. Start with `excel-xlsm-contract-ops`, treat live-state and unsaved-edit risk explicitly, and block or warn before any formatting or VBA stage if safety is not confirmed.
