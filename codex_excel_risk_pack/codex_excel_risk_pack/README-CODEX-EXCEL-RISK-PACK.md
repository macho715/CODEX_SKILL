# Codex Excel High-Risk Pack

## 목적

이 패키지는 OpenAI Codex에서 다음 조합을 **최상위 고위험 Excel 계약 민감 작업**으로 다루기 위한 최소 운영 세트다.

- 기존 `.xlsm`
- Python + VBA 혼합 변경
- COM automation 또는 VBA reinjection
- `Application.Run`
- save → close → reopen 검증
- non-ASCII 경로, 파일명, sheet name, caption
- button / shape / `OnAction` / event handler / named range / `ListObject` / formula 위치 변경
- 이미 열려 있는 workbook
- unsaved changes 가능성
- 파일은 생성되지만 매크로 실행 또는 런타임 검증이 나중에 깨지는 패턴

## 구성 원칙

- `AGENTS.md`: Codex가 따라야 할 저장소 규칙
- `heartbeat.md`: 상태 보고 전용
- `.codex/agents/*.toml`: 역할 분리된 custom agent
- `.agents/skills/**/SKILL.md`: 반복 절차를 캡슐화한 Skill
- `docs/ops/*`: 운영 runbook, 체크리스트, prompt 예시, benchmark 노트

## 설치 순서

1. 저장소 루트에 `AGENTS.md`와 `heartbeat.md`를 둔다.
2. `.codex/config.toml`과 `.codex/agents/*.toml`을 복사한다.
3. `.agents/skills/excel-xlsm-contract-ops/` 전체를 복사한다.
4. `docs/ops/` 문서를 팀 운영용으로 공유한다.
5. Codex를 다시 시작하거나 새 세션을 열어 변경을 반영한다.

## 사용 순서

### 기본
- 일반 작업: 루트 `AGENTS.md`만으로 시작
- 고위험 Excel 작업: `$excel-xlsm-contract-ops` 또는 관련 지시로 Skill 호출
- 병렬이 필요하면 explicit subagent prompt 사용

### 권장 explicit prompt
```text
Use explicit subagent workflows.
Have manager decompose the task.
Have guardrail inspect live workbook risk, Unicode risk, reinjection risk, and collision risk.
Have implementer apply a single-writer patch only after guardrail clears the plan.
Have verifier run save-close-reopen, compile, workbook-qualified Application.Run, and output checks.
Update heartbeat.md at every major stage.
```

## 운영 요약

- 병렬은 **read-heavy / analysis-heavy** 단계에 우선 적용
- 실제 workbook write는 **single-writer**
- `HEARTBEAT_DONE`은 파일 생성이 아니라 **검증 완료**를 의미
- open workbook + unsaved changes + reinjection + non-ASCII + Python/VBA 혼합이면 기본 `WARN` 이상
