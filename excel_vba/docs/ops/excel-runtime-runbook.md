# Excel Runtime Runbook

## Purpose

Use this runbook for existing `.xlsm` work, Python and VBA mixed changes, VBA reinjection, `Application.Run`, Unicode path handling, and live workbook risk.

## 0. Precheck

Confirm:

- target workbook path
- whether the workbook is already open
- whether unsaved changes are present
- write scope
- touched surfaces
- target macro entrypoint
- whether the path, caption, or sheet name is non-ASCII
- whether Python changes workbook structure
- whether VBA reinjection is required

Output:

- risk class
- write posture
- validation plan

## 1. Risk Classification

Treat these as high risk:

- existing `.xlsm`
- Python and VBA mixed mutation
- COM
- reinjection
- non-ASCII
- live workbook
- contract-sensitive surface touched

Treat these as blocked until clarified:

- unsaved state unknown on a live workbook
- blind overwrite would touch a live session
- same-workbook same-surface parallel write
- compile or references unknown after reinjection
- macro entrypoint unknown but `Application.Run` is required

## 2. Choose Execution Posture

### Read-only diagnosis

Use this for:

- workbook state review
- collision review
- Unicode risk review
- prompt preparation

### Serial single-writer patch

Use this for:

- direct workbook patching
- VBA reinjection
- Python and VBA contract reconciliation

### Blocked

Use this for:

- live workbook safety concerns
- approval gaps
- missing required inputs

## 3. Patch Rules

- patch in place first
- avoid structure rebuild unless explicitly requested
- do not force close
- do not discard unsaved edits
- if the surface is contract-sensitive, do not route it through a formatting-only workflow

## 4. Validation Gates

### Always

- workbook open
- save
- close
- reopen
- output integrity

### If VBA changed

- compile
- references
- workbook-qualified `Application.Run`

### If controls or events changed

- button
- shape
- `OnAction`
- worksheet or workbook event
- named range
- `ListObject`

### If Python coexists

- sheet name
- `Result`
- `Validation_Errors`
- `LOG`
- formula location
- macro preservation

## 5. Heartbeat Policy

Suggested stages:

- `PRECHECK`
- `PATCH`
- `INJECT`
- `SAVE`
- `REOPEN`
- `RUN`
- `VERIFY`
- `DONE`

Minimum update points:

1. after risk classification
2. before write
3. after save
4. after reopen
5. after `Application.Run`
6. before final validation

## 6. Handoff Contract

### guardrail to implementer

- risk class
- live workbook state
- collision surfaces
- required approvals
- single-writer decision
- validation gates

### implementer to verifier

- surfaces touched
- reinjection status
- expected macro entrypoint
- expected output artifacts
- known residual risks

### verifier to manager or user

- verified
- failed or unverified
- final heartbeat state
- next action

## 7. Done Definition

Mark the run done only when all of the following are satisfied:

- user work is preserved
- workbook state is safely handled
- compile and references pass if applicable
- save-close-reopen passes
- workbook-qualified `Application.Run` passes if applicable
- output integrity passes
- no hidden blocker remains

