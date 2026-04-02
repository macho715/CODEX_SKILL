---
name: mstack-qa
description: >
  Verification-only QA skill for Codex. Use when the main task is to choose a
  test mode, run or specify tests, summarize pass/fail results, and propose
  regression coverage after code changes or before release; triggers include
  qa, validate, smoke, regression, coverage, and test-result requests. Prefer
  `mstack-investigate` when the main task is root-cause analysis for a failure,
  and prefer `mstack-pipeline` when the user wants verification chained with
  planning, review, shipping, and retro.
---

# QA 검증

## Use This Skill When

- the main task is verification, test selection, or regression coverage after
  code changes
- the user asks for diff-aware, full, or quick validation
- release readiness depends on test outcomes rather than design or root cause

## Prefer Another Skill When

- the failure needs root-cause analysis: use `mstack-investigate`
- the user wants a multi-stage chain including review, ship, or retro: use
  `mstack-pipeline`
- the implementation plan is still missing: use `mstack-plan`

## 3가지 모드

사용자가 모드를 지정하지 않으면 상황에 맞게 자동 선택한다.

| 모드 | 언제 | 무엇을 |
|------|------|--------|
| `Diff-aware` | 배포 직후 또는 변경이 좁을 때 | 변경된 파일과 관련된 테스트만 실행 |
| `Full` | 전체 검증이 필요할 때 | 전체 테스트 스위트 실행 |
| `Quick` | 빠르게 확인할 때 | 핵심 경로 테스트만 실행 |

## 실행 절차

### Step 1 - 모드 결정

```text
배포 직후 또는 변경 범위가 좁은가?
  ├─ Yes → Diff-aware
  └─ No → 사용자 요청 분석
          ├─ "전체" / "full" → Full
          ├─ "빠르게" / "quick" / "smoke" → Quick
          └─ 불명확 → Diff-aware
```

### Step 2 - 테스트 실행

#### Diff-aware 모드

```bash
CHANGED=$(git diff --name-only HEAD~1)
# Python: pytest --co -q 로 관련 테스트를 찾는다.
# TypeScript: jest --findRelatedTests $CHANGED
```

#### Full 모드

```bash
# 프로젝트 표준 테스트 명령어를 실행한다.
{test_command}
```

#### Quick 모드

```bash
# 마커/태그 기반 또는 핵심 파일만 실행한다.
```

### Step 3 - 결과 분석

테스트 결과를 파싱하여 다음을 기록한다.
- 통과한 테스트 수
- 실패한 테스트 목록
- 스킵된 테스트와 이유
- 실행 시간

### Step 4 - 회귀 테스트 제안

새로 추가되거나 수정된 함수 중 테스트가 없는 것을 감지하면 다음을 제안한다.
1. 함수 시그니처와 docstring을 확인한다.
2. 정상 경로와 에러 경로를 설계한다.
3. `tests/` 파일을 생성하기 전에 사용자에게 먼저 보여준다.

```markdown
## 회귀 테스트 제안
- `test_new_function_happy_path`
- `test_new_function_edge_empty`
- `test_new_function_edge_large`
```

### Step 5 - QA 리포트

```markdown
# QA Report
Date: YYYY-MM-DD
Mode: Diff-aware | Full | Quick

## Results
- Total: N tests
- Passed: X
- Failed: Y
- Skipped: Z
- Duration: Xs

## Failures
1. test_name — error message

## Regression Tests Generated
- N개 새 테스트 제안됨

## Verdict
- [ ] PASS
- [ ] FAIL
```

## 실패 시 분기

테스트 실패가 발견되면 원인 분석을 시작하거나, 수정 후 다시 실행할 수 있게 안내한다.

## 성공 시 분기

모든 테스트 통과 시 회고를 작성할 수 있게 안내한다.

## Guardrails

- 실패 원인은 테스트 이름과 함께 적는다.
- 회귀 테스트는 생성 전 제안 형태로 제시한다.
- 검증 명령이 불명확하면 프로젝트 표준 테스트 명령부터 찾는다.
