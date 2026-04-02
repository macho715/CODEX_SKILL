---
name: mstack-pipeline
description: >
  End-to-end SDLC 오케스트레이션 스킬. 하나의 요청을 careful, dispatch, plan 또는
  investigate, 구현, review, QA, ship, retro까지 전 단계를 자동 체이닝한다.
  이 스킬은 pipeline, "한 번에", "end-to-end", "자동으로 끝까지",
  "전체 파이프라인", "처음부터 끝까지", "한방에 해줘" 등
  다단계 SDLC 자동 실행이 필요한 모든 상황에서 반드시 사용해야 한다.
  단일 단계만 필요하면 해당 스킬을 직접 사용하라:
  설계만 → mstack-plan, 리뷰만 → mstack-review, 검증만 → mstack-qa.
  mstack SDLC 파이프라인의 전 단계를 관통하는 최상위 오케스트레이터.
---

# /pipeline — End-to-End 오케스트레이터

> 파이프라인 위치: 전 단계를 관통하는 **최상위 오케스트레이터**

## Use This Skill When

- 하나의 요청을 planning/investigation → 구현 → review → QA → ship → retro까지
  한 번에 실행해야 할 때
- 사용자가 "end-to-end", "한 번에", "자동으로 끝까지" 등을 요청할 때
- 다단계 자동 체이닝이 필요하고 개별 스킬 호출로는 번거로울 때

## Prefer Another Skill When

- 설계/승인만 필요: `mstack-plan` 사용
- 리뷰/diff 검토만 필요: `mstack-review` 사용
- 검증/테스트만 필요: `mstack-qa` 사용
- 단순 설명, 상태 요약, 메타 분석: 스킬 없이 직접 응답

---

## 1. 작업 분류

| 작업 유형 | 키워드 | 진입 경로 |
|----------|--------|----------|
| `feature` | 신규 기능, 추가, 생성 | planning path |
| `refactor` | 리팩터링, 정리, 분리 | planning path |
| `bugfix` | 버그, 수정, 크래시, 에러 | investigation path |
| `deploy` | 배포, 릴리스, 머지 | release path |
| `test` | 검증, 테스트, validate | QA-only path |
| `retro` | 회고, 정리, 마무리 | retrospective-only path |

## 2. 글로벌 가드레일 적용

- `mstack-careful`로 안전 자세를 먼저 설정한다.
- `mstack-dispatch`로 실행 모드를 결정한다 (SINGLE/SUBAGENT/AGENT_TEAMS).
- 파괴적 동작, 시크릿 노출, protected branch 위험이 있으면 즉시 중단한다.

## 3. 스테이지 체인

| 작업 유형 | 실행 순서 |
|----------|----------|
| `feature` | careful → dispatch → plan → implement → review → qa → ship → retro |
| `refactor` | careful → dispatch → plan → implement → review → qa → ship → retro |
| `bugfix` | careful → dispatch → investigate → implement → qa → ship → retro |
| `deploy` | careful → dispatch → ship → qa → retro |
| `test` | careful → dispatch → qa |
| `retro` | retro |

## 4. 재시도 및 중단 규칙

- `qa` 실패 시 → `review → fix → qa` 재시도 (최대 3회)
- `qa` 실패 중에는 `ship`으로 진행하지 않는다.
- 보안/시크릿/protected-branch 블로커가 해결되지 않으면 중단한다.
- 사용자가 체크포인트를 요청하면 현재 스테이지 완료 후 정지 + 상태 보고.

## 5. 자동 실행 흐름 (feature 예시)

```
1. /careful 적용 → 안전 자세 설정
2. /dispatch 실행 → 모드 결정 (SINGLE/SUBAGENT/AGENT_TEAMS)
3. /plan 실행 → plan.md 생성
4. 사용자 승인 대기 (유일한 개입 지점)
5. 승인 후 자동 체이닝:
   ├─ 구현 실행
   ├─ /review 자동 실행 → AUTO-FIX 적용
   ├─ /qa 실행
   │   ├─ PASS → /ship 자동 커밋 → /retro 실행
   │   └─ FAIL → 재시도 사이클 (최대 3회)
   │       ├─ review → 원인 분석 → 수정 → qa 재실행
   │       └─ 3회 실패 → 파이프라인 중단 + 결과 보고
6. memory.py로 세션 결과 자동 저장
```

## 6. 출력 형식

```markdown
# Pipeline Summary
Work type: feature | bugfix | refactor | deploy | test | retro
Execution mode: SINGLE | SUBAGENT | AGENT_TEAMS
Stage order: careful → dispatch → plan → implement → review → qa → ship → retro

## Results
- Files changed: N개
- Blockers: 없음 | [목록]
- Retries used: 0/3
- Final status: PASS | FAIL | STOPPED
- Next action: [다음 추천 행동]
```

## 7. 기본 동작

- `plan` 후 사용자 승인 게이트가 기본값이다. 생략 요청 시 자동 진행.
- 중간 스테이지 노트는 짧게 유지한다.
- 추론으로 컨텍스트를 보완한 경우 가정사항을 명시한다.
- `core/pipeline.py`의 `PipelineResult`가 사용 가능하면 엔진 요약 필드 사용.
- 결정적 구현 레시피에 맞지 않는 요청은 `mstack pipeline --generic-implement notes`로
  안전한 fallback 사용.

## core/pipeline.py 연동

`execute_pipeline()` 호출 시:
- `PIPELINE_TEMPLATES`의 스테이지 순서를 따른다.
- `AUTO_RETRY_STAGES`의 재시도 설정을 준수한다.
- `MAX_RETRIES` (기본 3)를 초과하면 파이프라인을 중단한다.
- `STAGE_TO_SKILL` 매핑으로 각 스테이지에 해당하는 스킬을 선택한다.
- 결과는 `core/memory.py`를 통해 세션 메모리에 자동 저장된다.

---

## mstack 파이프라인 스킬 참조
- mstack-plan → mstack-review → mstack-ship → mstack-qa → mstack-investigate → mstack-retro
- mstack-careful: 모든 단계에 적용 가능한 안전 가드레일
- mstack-dispatch: 전 파이프라인 진입점 오케스트레이터
- mstack-pipeline (현재): 전 단계를 관통하는 최상위 오케스트레이터
