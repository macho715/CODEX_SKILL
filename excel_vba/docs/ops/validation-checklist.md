# Validation Checklist

## A. Risk Classification

- existing `.xlsm`
- Python and VBA mixed mutation
- COM automation
- VBA reinjection
- `Application.Run`
- non-ASCII path, filename, caption, or sheet name
- live workbook
- unsaved changes risk
- button, shape, or `OnAction`
- worksheet or workbook event
- named range or `ListObject`
- formula-bearing contract surface

## B. Safety Gate

- force close is prohibited
- blind overwrite is prohibited
- discarding unsaved user edits is prohibited
- same-workbook same-surface parallel write is prohibited
- approval is required when the surface is high risk
- heartbeat stage must be started before runtime mutation

## C. Implementation Gate

- patch-in-place is the default
- structure rebuild is only allowed when explicitly requested
- list touched surfaces before changing anything
- run a Python and VBA collision review when both coexist
- call out non-ASCII risk explicitly

## D. Verification Gate

- workbook open
- save
- close
- reopen
- compile if applicable
- references if applicable
- workbook-qualified `Application.Run` if applicable
- named range integrity
- `ListObject` integrity
- control, button, shape, and `OnAction` integrity
- event handler integrity
- `Result` integrity if applicable
- `Validation_Errors` integrity if applicable
- `LOG` integrity if applicable
- no hidden blocker remains

## E. Completion Gate

- `HEARTBEAT_DONE` is appropriate for the run
- file creation alone is not completion
- save success alone is not completion
- reopen success alone is not completion

