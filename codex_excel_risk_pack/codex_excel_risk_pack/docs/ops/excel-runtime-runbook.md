# Excel Runtime Runbook

## 목적

기존 `.xlsm`에 대한 Python/VBA 혼합 변경, VBA reinjection, `Application.Run`, Unicode path, live workbook 이슈를 안전하게 처리하기 위한 운영 runbook이다.

## 0. Precheck

확인 항목:
- target workbook path
- workbook open 여부
- unsaved changes 여부
- write scope
- touched surfaces
- target macro entrypoint
- non-ASCII path / caption / sheet name 존재 여부
- Python이 workbook structure를 바꾸는지
- VBA reinjection 필요 여부

산출:
- Risk class
- write posture
- validation plan

## 1. Risk classify

최소 HIGH로 분류:
- existing `.xlsm`
- Python + VBA mixed mutation
- COM
- reinjection
- non-ASCII
- live workbook
- contract-sensitive surface touched

즉시 BLOCKED 후보:
- unsaved state unknown on live workbook
- blind overwrite would touch live session
- same workbook same-surface parallel write
- compile or references unknown after reinjection
- macro entrypoint unknown but `Application.Run` required

## 2. Choose execution posture

### Read-only diagnosis
사용 시점:
- workbook state 조사
- collision review
- Unicode risk review
- prompt 준비

### Serial single-writer patch
사용 시점:
- 실제 workbook patch
- VBA reinjection
- Python/VBA contract reconciliation

### Blocked
사용 시점:
- live workbook 보호가 우선
- approval 불가
- 필수 입력 부족

## 3. Patch rules

- patch-in-place first
- structure rebuild 금지 unless explicitly requested
- force close 금지
- unsaved edit discard 금지
- formatting처럼 보여도 contract-sensitive surface면 formatting workflow 금지

## 4. Validation gates

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

### If controls/events changed
- button
- shape
- `OnAction`
- worksheet/workbook event
- named range
- `ListObject`

### If Python coexists
- sheet name
- Result
- Validation_Errors
- LOG
- formula location
- macro preservation

## 5. Heartbeat policy

권장 stage:
- `PRECHECK`
- `PATCH`
- `INJECT`
- `SAVE`
- `REOPEN`
- `RUN`
- `VERIFY`
- `DONE`

최소 업데이트 시점:
1. risk classify 완료 직후
2. write 시작 직전
3. save 이후
4. reopen 이후
5. `Application.Run` 이후
6. 최종 검증 이후

## 6. Handoff contract

### guardrail → implementer
- risk class
- live workbook state
- collision surfaces
- required approvals
- single-writer 여부
- validation gates

### implementer → verifier
- surfaces touched
- reinjection 여부
- expected macro entrypoint
- expected output artifacts
- known residual risks

### verifier → manager/user
- verified
- failed or unverified
- final heartbeat state
- next action

## 7. Done definition

아래를 모두 만족할 때만 Done:
- user work preserved
- workbook state safely handled
- compile / references passed if applicable
- save-close-reopen passed
- workbook-qualified `Application.Run` passed if applicable
- output integrity passed
- hidden blocker 없음
