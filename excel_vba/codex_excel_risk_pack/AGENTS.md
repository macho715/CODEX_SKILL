# AGENTS.md

## Repository Operating Rule

이 저장소는 Codex로 **고위험 Excel 계약 민감 작업**을 수행하는 저장소다.

핵심 원칙:
- 파일 생성은 완료가 아니다.
- save 성공은 완료가 아니다.
- reopen 성공은 완료가 아니다.
- Excel 작업의 완료는 검증까지 끝난 상태만 의미한다.
- 고위험 workbook write는 single-writer 원칙을 따른다.

## Scope

이 문서는 저장소 루트 기본 규칙이다.
더 좁은 디렉터리에서 `AGENTS.override.md`가 있으면 그 규칙이 우선한다.

## High-Risk Excel Contract Surface

다음 조합은 최상위 고위험 케이스로 간주한다.

- existing `.xlsm`
- Python + VBA mixed mutation
- COM automation or VBA reinjection
- non-ASCII path, filename, sheet name, module name, caption, or button text
- `Application.Run`
- button / shape / `OnAction`
- worksheet / workbook event handler
- named range / `ListObject` / table name
- formula-bearing contract surface
- live workbook state
- possible unsaved changes
- patch-in-place on an already open workbook

이 케이스는 formatting처럼 보여도 formatting이 아니다.
이 케이스는 **contract-sensitive workbook surgery**다.

## Mandatory execution posture

- 기본은 `patch-in-place`
- 구조 재생성 또는 workbook replacement는 기본 금지
- open workbook을 강제 close 하지 않는다
- unsaved user edits를 버리지 않는다
- workbook state, lock state, unsaved state가 불명확하면 리스크 상승으로 처리한다
- open workbook overwrite / blind reinjection 금지
- save 전후에 hidden failure 가능성을 항상 의심한다

## Mandatory validation gate

고위험 Excel 작업에서 완료 주장은 아래 검증이 끝난 뒤에만 가능하다.

1. workbook open
2. patch or reinjection result
3. compile check if VBA changed
4. references check if VBA changed
5. named range / table / control binding / event binding check
6. save
7. close
8. reopen
9. workbook-qualified `Application.Run`
10. output integrity check
11. hidden blocker 없음 확인

## Truthfulness rule

다음 상태는 모두 완료가 아니다.

- 파일만 생성됨
- save만 성공함
- reopen만 성공함
- compile 미확인
- `Application.Run` 미확인
- `Result` / `Validation_Errors` / `LOG` 미확인

## Heartbeat policy

이 저장소는 `heartbeat.md`를 운영 상태 보고 문서로 사용한다.

반드시 heartbeat를 사용해야 하는 경우:
- Excel COM automation
- VBA injection / reinjection
- `.xlsm` patch
- Python↔Excel bridge
- non-ASCII path or caption
- live workbook
- unsaved changes risk
- spawned subagent workflow
- save 이후 숨은 실패 가능성이 있는 경우

허용 상태:
- `HEARTBEAT_OK`
- `HEARTBEAT_WARN`
- `HEARTBEAT_BLOCKED`
- `HEARTBEAT_DONE`

형식은 `heartbeat.md`를 따른다.

## Parallel rule

기본 계획 자세는 `parallel-preferred`다.
단, 고위험 Excel write 단계는 parallel-by-default가 아니다.

허용:
- parallel read-only analysis
- parallel collision review
- parallel validation planning
- parallel documentation or evidence gathering

기본 금지:
- same workbook parallel write
- same VBA project parallel write
- same worksheet event code parallel write
- same named range / table / control surface parallel write

## Explicit subagent workflow

Codex subagent는 명시 요청 시에만 spawn한다고 가정한다.
따라서 병렬이 필요하면 명시적으로 요청한다.

권장 역할:
- `manager`: 작업 분해, lane 조정, merge 판단
- `guardrail`: live workbook, lock, Unicode, collision, approval, hidden failure risk 점검
- `implementer`: single-writer patch execution
- `verifier`: save-close-reopen, compile, `Application.Run`, output 검증

## Approval and sandbox

- 승인 없이 destructive action 금지
- 승인 없이 blind overwrite 금지
- 승인 없이 live workbook close 금지
- 고위험 run에서 approval이 새로 필요하지만 surface 할 수 없으면 `BLOCKED`
- sandbox는 기본적으로 최소 권한을 유지한다

## Skill routing

다음 조건이면 `excel-xlsm-contract-ops` Skill을 우선 사용한다.

- `.xlsm`
- VBA reinjection
- `Application.Run`
- COM automation
- Python + VBA coexistence
- non-ASCII path / caption
- button / shape / event / named range / table name / formula contract surface
- live workbook with possible unsaved changes

## Completion rule

다음이 모두 참일 때만 완료라고 쓴다.

- workbook state safely handled
- no unsaved user work discarded
- reinjection verified if used
- compile passed if VBA changed
- references passed if VBA changed
- bindings survived if controls / shapes / events changed
- save-close-reopen passed
- workbook-qualified `Application.Run` passed
- `Result`, `Validation_Errors`, `LOG` integrity checked when applicable
- no hidden blocker remains

## One-line operating summary

이 저장소에서 가장 위험한 케이스는
**기존 `.xlsm` + Python/VBA 혼합 변경 + control/event/named-range edit + non-ASCII path/caption + live workbook state** 이다.

항상 guarded contract-sensitive operation으로 취급한다.
