# heartbeat.md
# Codex Excel Runtime Heartbeat

## 목적

이 문서는 장시간 또는 숨은 실패가 잦은 Excel 작업에서 현재 상태를 짧고 일관되게 보고하기 위한 문서다.

이 문서의 역할:
- 현재 단계 표시
- 완료된 핵심 항목 표시
- blocker 표시
- 다음 행동 1개 표시
- live workbook / reinjection / Unicode / `Application.Run` / reopen 검증 상태 가시화

이 문서는 하지 않는 일:
- 장문 정책 작성
- 전체 로그 덤프
- 민감정보 저장
- 규칙 파일 대체

## 사용 조건

다음 중 하나면 heartbeat를 사용한다.

1. Excel COM automation
2. `.xlsm` patch 또는 VBA reinjection
3. Python↔Excel bridge
4. non-ASCII path / filename / sheet name / caption
5. button / shape / `OnAction` / event / named range / table binding 변경
6. live workbook
7. unsaved changes risk
8. explicit subagent workflow
9. 파일은 생겼지만 runtime integrity가 아직 미검증인 경우

## 허용 상태

- `HEARTBEAT_OK`
- `HEARTBEAT_WARN`
- `HEARTBEAT_BLOCKED`
- `HEARTBEAT_DONE`

## Stage 표준

- `PRECHECK`
- `OPEN`
- `PATCH`
- `INJECT`
- `SAVE`
- `REOPEN`
- `RUN`
- `VERIFY`
- `MERGE`
- `DONE`

## 형식

모든 heartbeat는 아래 형식을 사용한다.

```text
Status: <HEARTBEAT_OK | HEARTBEAT_WARN | HEARTBEAT_BLOCKED | HEARTBEAT_DONE>
Stage: <PRECHECK | OPEN | PATCH | INJECT | SAVE | REOPEN | RUN | VERIFY | MERGE | DONE>
Done:
- <item 1>
- <item 2>
- <item 3>
Blocker: <NONE or blocker>
Next: <one immediate next action>
```

`HEARTBEAT_BLOCKED`일 때만 아래를 추가한다.

```text
Input Required:
1. <required input 1>
2. <required input 2>
3. <required input 3>
```

## 강제 상승 규칙

다음 중 하나면 최소 `HEARTBEAT_WARN` 이상:
- save는 됐지만 reopen 미검증
- reopen은 됐지만 `Application.Run` 미검증
- compile 미검증
- references 미검증
- Unicode-sensitive path/caption 존재
- Python/VBA collision review 미완료
- live workbook state 미확정
- output integrity 미확인

다음 중 하나면 `HEARTBEAT_BLOCKED`:
- workbook is open and unsaved state unknown
- blind overwrite would touch live user session
- COM attach failed
- VBA import/reinjection failed
- compile failed
- references broken
- workbook-qualified `Application.Run` failed
- same workbook parallel write collision
- binding collision unresolved
- approval cannot be surfaced but is required

## Excel 점검 축

### Session / Process
- `Excel.exe` 잔존 여부
- invisible Excel instance
- workbook lock
- duplicate open session

### COM / Injection
- COM attach
- module import / reinjection
- compile
- references

### Workbook / Macro
- workbook open
- named range
- `ListObject`
- control binding
- event handler
- workbook-qualified `Application.Run`

### Python ↔ VBA
- sheet name
- `Result`
- `Validation_Errors`
- `LOG`
- formula location
- macro preservation
- structure mismatch

### Output / Evidence
- Result artifact 존재
- Validation artifact 존재
- log artifact 존재
- hidden blocker 없음

## 완료 정의

`HEARTBEAT_DONE`은 아래가 모두 끝난 경우만 사용한다.

- save
- close
- reopen
- compile if applicable
- references if applicable
- workbook-qualified `Application.Run` if applicable
- output integrity check

## 예시

### 정상 진행
```text
Status: HEARTBEAT_OK
Stage: PATCH
Done:
- workbook contract 확인
- collision surface 식별
- patch plan 확정
Blocker: NONE
Next: single-writer patch 적용
```

### 숨은 실패 의심
```text
Status: HEARTBEAT_WARN
Stage: REOPEN
Done:
- save 완료
- reopen 완료
- workbook open 확인
Blocker: macro run evidence 없음
Next: workbook-qualified Application.Run 검증
```

### live workbook blocker
```text
Status: HEARTBEAT_BLOCKED
Stage: PRECHECK
Done:
- target workbook 식별
- live session 존재 확인
- overwrite risk 식별
Blocker: unsaved changes state unknown on open workbook
Next: workbook 보존 전략 확인 후 진행 여부 결정
Input Required:
1. 현재 workbook에 unsaved edit가 있는지
2. live session patch 허용 여부
3. safe copy path 허용 여부
```

### 최종 완료
```text
Status: HEARTBEAT_DONE
Stage: DONE
Done:
- save-close-reopen 완료
- Application.Run 완료
- Result / Validation_Errors / LOG 확인
Blocker: NONE
Next: 사용자 검토 또는 다음 작업
```
