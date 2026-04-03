# Validation Checklist

## A. Risk classification

- [ ] existing `.xlsm`
- [ ] Python + VBA mixed mutation
- [ ] COM automation
- [ ] VBA reinjection
- [ ] `Application.Run`
- [ ] non-ASCII path / filename / caption / sheet name
- [ ] live workbook
- [ ] unsaved changes risk
- [ ] button / shape / `OnAction`
- [ ] worksheet / workbook event
- [ ] named range / `ListObject`
- [ ] formula-bearing contract surface

## B. Safety gate

- [ ] force close 금지 확인
- [ ] blind overwrite 금지 확인
- [ ] unsaved user edits discard 금지 확인
- [ ] same workbook same-surface parallel write 금지 확인
- [ ] approval 필요 여부 확인
- [ ] heartbeat stage 시작 여부 확인

## C. Implementation gate

- [ ] patch-in-place 사용
- [ ] structure rebuild 미사용 또는 명시 승인 확보
- [ ] touched surfaces 목록화
- [ ] Python/VBA collision review 수행
- [ ] non-ASCII risk 표시

## D. Verification gate

- [ ] workbook open
- [ ] save
- [ ] close
- [ ] reopen
- [ ] compile if applicable
- [ ] references if applicable
- [ ] workbook-qualified `Application.Run` if applicable
- [ ] named range integrity
- [ ] `ListObject` integrity
- [ ] control / button / shape / `OnAction` integrity
- [ ] event handler integrity
- [ ] `Result` integrity if applicable
- [ ] `Validation_Errors` integrity if applicable
- [ ] `LOG` integrity if applicable
- [ ] hidden blocker 없음

## E. Completion gate

- [ ] `HEARTBEAT_DONE` 사용 조건 충족
- [ ] file creation과 completion을 혼동하지 않음
- [ ] save success와 completion을 혼동하지 않음
- [ ] reopen success와 completion을 혼동하지 않음
