---
name: mstack-qa
description: >
  QA 검증 스킬. Diff-aware(변경 범위만), Full(전체), Quick(스모크) 3가지 모드로 테스트를 실행하고
  회귀 테스트를 자동 생성한다. 배포 후 검증 또는 독립 QA 세션 모두 지원.
  이 스킬은 qa, QA, 테스트, test, 검증, validate, regression, 회귀, "테스트 돌려줘",
  "깨진 거 없나", "전체 테스트", smoke test, "통과하나", "테스트 결과", test coverage,
  커버리지, "회귀 테스트 만들어줘" 등 테스트 실행/검증/회귀 방지가 필요한 모든 상황에서
  반드시 사용해야 한다. 코드 변경 후 검증이 필요하면 사용자가 명시적으로 요청하지 않아도
  이 스킬을 사용하라. mstack SDLC 파이프라인에서 /ship 후 실행되며, 버그 발견 시
  /investigate로 이어진다.
---

# /qa — QA 검증

> 파이프라인 위치: plan → review → ship → **[qa]** → investigate → retro

## 3가지 모드

사용자가 모드를 지정하지 않으면 컨텍스트에서 자동 선택한다:

| 모드 | 언제 | 무엇을 |
|------|------|--------|
| **Diff-aware** | `/ship` 직후 또는 PR 컨텍스트 | 변경된 파일과 관련된 테스트만 실행 |
| **Full** | "전체 테스트", 릴리스 전 | 전체 테스트 스위트 실행 |
| **Quick** | "빠르게 확인", 스모크 테스트 | 핵심 경로 테스트만 (마킹 기준) |

---

## 실행 절차

### Step 1 — 모드 결정

```
/ship 직후?
  ├─ Yes → Diff-aware
  └─ No → 사용자 요청 분석
          ├─ "전체" / "full" → Full
          ├─ "빠르게" / "quick" / "smoke" → Quick
          └─ 불명확 → Diff-aware (기본값)
```

### Step 2 — 테스트 실행

#### Diff-aware 모드
```bash
# 변경 파일 기반 관련 테스트 탐색
CHANGED=$(git diff --name-only HEAD~1)
# Python: pytest --co -q 로 테스트 디스커버리 후 관련 파일 필터
# TypeScript: jest --findRelatedTests $CHANGED
```

#### Full 모드
```bash
# CLAUDE.md의 테스트 명령어 실행
{test_command}
```

#### Quick 모드
```bash
# 마커/태그 기반 (pytest -m smoke / jest --tag=smoke)
# 마커가 없으면 tests/ 최상위 파일만 실행
```

### Step 3 — 결과 분석

테스트 결과를 파싱하여:
- ✅ 통과한 테스트 수
- ❌ 실패한 테스트 목록 (파일:줄, 에러 메시지 요약)
- ⏭️ 스킵된 테스트 (이유 포함)
- ⏱️ 실행 시간

### Step 4 — 회귀 테스트 자동 생성

새로 추가되거나 수정된 함수 중 테스트가 없는 것을 감지하면:

1. 해당 함수의 시그니처와 docstring을 읽는다
2. 정상 경로 + 에러 경로 테스트를 생성한다
3. `tests/` 디렉토리에 파일을 생성하되, 사용자에게 먼저 보여준다

```markdown
## 회귀 테스트 제안
- `test_new_function_happy_path`: 정상 입력 → 기대 출력
- `test_new_function_edge_empty`: 빈 입력 → 적절한 에러
- `test_new_function_edge_large`: 대량 입력 → 타임아웃 없음

생성하시겠습니까? [Y/n]
```

### Step 5 — QA 리포트

```markdown
# QA Report
Date: YYYY-MM-DD
Mode: Diff-aware | Full | Quick

## Results
- Total: N tests
- Passed: X ✅
- Failed: Y ❌
- Skipped: Z ⏭️
- Duration: Xs

## Failures (if any)
1. test_name — error message (파일:줄)

## Regression Tests Generated
- N개 새 테스트 제안됨

## Verdict
- [ ] PASS — 모든 테스트 통과
- [ ] FAIL — 실패 항목 수정 필요
```

---

## 실패 시 파이프라인 분기

테스트 실패가 발견되면:
> "QA에서 N건 실패. `/investigate`로 원인 분석을 시작하시겠습니까?
> 또는 직접 수정 후 `/qa`를 다시 실행할 수 있습니다."

## 성공 시 파이프라인 연결

모든 테스트 통과 시:
> "QA 통과. `/retro`로 이번 작업의 회고를 작성하시겠습니까?"

## 파이프라인 자동 실행 연동

`core/pipeline.py`의 `execute_pipeline()`에서 호출될 때:
- qa FAIL → 자동으로 review→fix→qa 재시도 사이클 진입 (최대 3회)
- qa PASS → 다음 스테이지(ship/retro)로 자동 체이닝
- 결과는 `core/memory.py`를 통해 세션 메모리에 자동 저장됨

## mstack 파이프라인 스킬 참조
- mstack-plan → mstack-review → mstack-ship → mstack-qa (현재) → mstack-investigate → mstack-retro
- mstack-careful: 모든 단계에 적용 가능한 안전 가드레일
