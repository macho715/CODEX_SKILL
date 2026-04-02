# MStack Codex Skill 상세 가이드

이 문서는 이 저장소에 포함된 MStack Codex skill들을 실제 작업에서 어떻게
선택하고 호출할지 한 번에 정리한 사용자 가이드다.

대상 범위:
- `mstack-*` 전체
- `pipeline-coordinator`
- `orchestrate-analysis`
- `scenario-scorer`
- `analysis-verifier`

## 개요

MStack 계열은 역할이 다르다.

- `mstack-*`: SDLC 단계별 작업을 수행하는 운영 skill
- `pipeline-coordinator`: 복잡한 선택지를 병렬 비교하는 의사결정 엔진
- `orchestrate-analysis` / `scenario-scorer` / `analysis-verifier`:
  coordinator 안팎에서 분석, 점수화, 검증을 분리하는 분석 계열 skill

Codex에서 skill을 가장 확실하게 쓰는 방법은 요청에 skill 이름을 직접 넣는 것이다.

예:

```text
Use $mstack-plan to define scope and test strategy for this change.
Use $mstack-pipeline to handle this request end-to-end.
Use $pipeline-coordinator to compare three rollout options.
```

기본 원칙:
- 설계만 필요하면 `mstack-plan`
- 실패 원인부터 밝혀야 하면 `mstack-investigate`
- 검증만 필요하면 `mstack-qa`
- 코드 리뷰만 필요하면 `mstack-review`
- 끝까지 자동으로 몰아서 처리하려면 `mstack-pipeline`
- 3개 이상 옵션 비교나 큰 trade-off는 `pipeline-coordinator`

## 빠른 선택 가이드

| 상황 | 추천 skill |
|---|---|
| 안전 가드레일 먼저 필요 | `mstack-careful` |
| 직접 처리 vs 병렬 분배를 먼저 결정 | `mstack-dispatch` |
| 구현 전 설계, 범위, acceptance criteria 정리 | `mstack-plan` |
| 실패 원인, 재현, 가설 검증 먼저 | `mstack-investigate` |
| 계획부터 구현, 리뷰, QA, ship, retro까지 한 번에 | `mstack-pipeline` |
| 코드나 diff 리뷰만 | `mstack-review` |
| 검증만, 회귀 점검만 | `mstack-qa` |
| merge/push/deploy 직전 release gate | `mstack-ship` |
| 작업 종료 후 회고 | `mstack-retro` |
| 3개 이상 옵션 비교, 고위험 구조 선택 | `pipeline-coordinator` |
| 다관점 분석 artifact 생성 | `orchestrate-analysis` |
| 옵션 점수화 | `scenario-scorer` |
| 분석 결과 PASS/FAIL 검증 | `analysis-verifier` |

## 전체 스킬 표

| 스킬 | 언제 쓰는지 | 언제 쓰지 말아야 하는지 | 한 줄 프롬프트 예시 |
|---|---|---|---|
| `mstack-careful` | 파괴적 변경, 시크릿, protected branch, rollback 위험이 있어서 안전 경계부터 세워야 할 때 | 이미 안전 범위가 분명한 단순 작업일 때 | `Use $mstack-careful to set guardrails before changing release automation.` |
| `mstack-dispatch` | 직접 처리, 병렬 분배, ownership 결정을 먼저 해야 할 때 | 구현 자체를 바로 시작하면 되는 작은 작업일 때 | `Use $mstack-dispatch to split this cross-module refactor into safe ownership lanes.` |
| `mstack-plan` | 구현 전에 범위, 파일 변경, acceptance criteria, 테스트 전략을 확정할 때 | 이미 코드가 있고 리뷰나 QA가 주목적일 때 | `Use $mstack-plan to define scope and test strategy for this migration.` |
| `mstack-investigate` | 실패 원인, 재현, 가설 검증이 먼저일 때 | 원인이 이미 명확하고 수정이나 QA만 남았을 때 | `Use $mstack-investigate to find why the Windows real toolchain test fails.` |
| `mstack-pipeline` | 계획, 구현, 리뷰, QA, ship, retro까지 한 요청을 끝까지 연결할 때 | 설계만, 리뷰만, QA만 같은 단일 단계 요청일 때 | `Use $mstack-pipeline to add CSV import end-to-end and carry it through QA.` |
| `mstack-review` | 바뀐 코드나 diff를 기준으로 버그, 회귀, 누락 테스트를 찾을 때 | 구현 전 설계 단계이거나 단순 테스트 실행만 필요할 때 | `Use $mstack-review to review the pipeline_runner patch for regressions.` |
| `mstack-qa` | 검증만 하고 싶을 때, 테스트 선택과 pass/fail 요약이 핵심일 때 | 원인 분석이 먼저이거나 end-to-end 체인이 필요할 때 | `Use $mstack-qa to run focused regression checks for the TypeScript flow.` |
| `mstack-ship` | merge, push, deploy 전 release gate를 확인할 때 | 아직 구현, 리뷰, QA가 끝나지 않았을 때 | `Use $mstack-ship to verify this branch is safe to merge.` |
| `mstack-retro` | 끝난 작업을 회고하고 교훈과 follow-up을 정리할 때 | 작업이 아직 진행 중이거나 먼저 QA/리뷰가 필요한 때 | `Use $mstack-retro to summarize lessons from the Windows PATH issue.` |
| `pipeline-coordinator` | 3개 이상 옵션 비교, 고위험 구조 선택, 큰 trade-off 판단을 병렬 의사결정으로 처리할 때 | 단순 버그 수정, 단일 구현안, 작은 설계 선택일 때 | `Use $pipeline-coordinator to compare three rollout options for this architecture change.` |
| `orchestrate-analysis` | 복잡한 문제를 여러 관점의 분석 artifact로 분해해야 할 때 | 이미 옵션이 정리돼 있고 점수화나 검증만 남았을 때 | `Use $orchestrate-analysis to break down migration options for the pipeline runtime.` |
| `scenario-scorer` | 3개 이상 옵션을 기준과 가중치로 재현 가능하게 점수화할 때 | 옵션이 1~2개뿐이거나 구현 자체가 핵심일 때 | `Use $scenario-scorer to rank plugin-first, direct install, and hybrid packaging.` |
| `analysis-verifier` | 분석, 설계안, coordinator 결과가 acceptance criteria를 충족하는지 PASS/FAIL로 검증할 때 | 아직 분석 초안 자체가 없을 때 | `Use $analysis-verifier to verify whether this recommendation meets the release criteria.` |

## 자주 쓰는 조합

### 1. 고위험 설계 선택

```text
Use $mstack-plan first, then $pipeline-coordinator, for this high-risk architecture decision: [decision].
Return the recommendation, scoring summary, verifier verdict, and remaining gaps.
```

추천 흐름:
- `mstack-plan`
- `pipeline-coordinator`
- 필요 시 `analysis-verifier`

### 2. 장애 원인 파악 후 수정

```text
Use $mstack-investigate first, then $mstack-pipeline, for this failure and fix flow: [issue].
```

추천 흐름:
- `mstack-investigate`
- `mstack-pipeline`

### 3. 코드 변경 후 릴리스 전 점검

```text
Use $mstack-review, then $mstack-qa, then $mstack-ship for this change: [branch or diff].
```

추천 흐름:
- `mstack-review`
- `mstack-qa`
- `mstack-ship`

### 4. 작업 분배 후 실행

```text
Use $mstack-dispatch first to split ownership, then $mstack-pipeline to execute: [task].
```

추천 흐름:
- `mstack-dispatch`
- `mstack-pipeline`

## 추천 프롬프트 템플릿

### 단일 skill 템플릿

```text
Use $mstack-careful to set guardrails before touching [target].
```

```text
Use $mstack-dispatch to decide whether this work should be done directly, split into lanes, or delegated: [task].
```

```text
Use $mstack-plan to define scope, file changes, acceptance criteria, and test strategy for: [task].
```

```text
Use $mstack-investigate to reproduce the issue, test hypotheses, and identify the root cause for: [issue].
```

```text
Use $mstack-review to review the current diff for bugs, regressions, and missing tests: [context].
```

```text
Use $mstack-qa to run focused validation for: [change or feature].
```

```text
Use $mstack-ship to verify merge or release readiness for: [branch/change].
```

```text
Use $mstack-retro to summarize lessons learned, outcomes, and follow-up actions for: [completed work].
```

```text
Use $mstack-pipeline to handle this request end-to-end: [task].
```

### 의사결정 / 분석 템플릿

```text
Use $pipeline-coordinator to compare multiple implementation options for: [decision].
Return the recommendation, scoring summary, verifier verdict, and remaining gaps.
```

```text
Use $orchestrate-analysis to break this problem into structured analysis workstreams: [problem].
```

```text
Use $scenario-scorer to rank these options with explicit criteria and weights: [options].
```

```text
Use $analysis-verifier to verify whether this analysis or plan satisfies the acceptance criteria: [artifact].
```

### 자주 쓰는 조합 템플릿

```text
Use $mstack-plan first, then $pipeline-coordinator, for this high-risk architecture decision: [decision].
```

```text
Use $mstack-investigate first, then $mstack-pipeline, for this failure and fix flow: [issue].
```

```text
Use $mstack-review, then $mstack-qa, then $mstack-ship for this change: [branch or diff].
```

```text
Use $mstack-dispatch first to split ownership, then $mstack-pipeline to execute: [task].
```

## 상황별 템플릿 세트

### 버그 수정

```text
Use $mstack-investigate to reproduce and identify the root cause for: [bug].
After that, use $mstack-pipeline to implement the fix, review it, run QA, and stop before ship if blockers remain.
```

짧은 버전:

```text
Use $mstack-pipeline to handle this bug end-to-end, but investigate root cause before editing code: [bug].
```

### 리팩터링

```text
Use $mstack-plan to define scope, file changes, risks, and test strategy for this refactor: [refactor].
Then use $mstack-pipeline to execute the approved refactor through review and QA.
```

고위험 구조 선택 포함:

```text
Use $mstack-plan first, then $pipeline-coordinator, to compare refactor options for: [refactor].
Return the recommendation, scoring summary, verifier verdict, and remaining gaps before implementation.
```

### 문서 작업

```text
Use $mstack-plan to define the target audience, scope, changed files, and acceptance criteria for this documentation update: [doc task].
Then implement the doc changes and review them for accuracy and drift.
```

문서만 빠르게:

```text
Use $mstack-plan for this documentation change and then update the docs directly: [doc task].
```

### 배포 전 점검

```text
Use $mstack-review, then $mstack-qa, then $mstack-ship for this branch or release candidate: [branch/change].
Focus on regressions, test outcomes, release blockers, and merge readiness.
```

끝까지 묶는 버전:

```text
Use $mstack-pipeline to take this release candidate through review, QA, ship, and retro: [release candidate].
```

## Coordinator / Analysis 계열 설명

### `pipeline-coordinator`

역할:
- 3개 이상 선택지를 병렬로 비교하는 고정 4-lane 의사결정 엔진
- 추천안, 점수 요약, verifier verdict, remaining gaps를 출력

적합한 경우:
- 아키텍처 선택
- 배포 전략 비교
- refactor 전략 비교
- 운영 trade-off가 큰 선택

부적합한 경우:
- 작은 버그 수정
- 구현안이 이미 하나로 확정된 경우

### `orchestrate-analysis`

역할:
- 큰 문제를 여러 관점의 분석 artifact로 나누는 분석 초안 생성기

### `scenario-scorer`

역할:
- 옵션을 기준과 가중치로 점수화하는 평가 lane

### `analysis-verifier`

역할:
- 분석 결과가 acceptance criteria를 만족하는지 PASS/FAIL로 검증하는 lane

### handoff 관계

가장 자연스러운 흐름:

```text
mstack-plan
-> pipeline-coordinator
-> orchestrate-analysis
-> scenario-scorer
-> analysis-verifier
-> coordinator final merge
```

현업 해석:
- `mstack`은 언제 무엇을 할지 정한다
- `pipeline-coordinator`는 복잡한 선택을 병렬 판단한다
- `orchestrate-analysis`는 분석 초안을 만든다
- `scenario-scorer`는 점수화한다
- `analysis-verifier`는 최종 검증한다

## Windows Node PATH 운영 참고

Windows에서 `npm install`, `npx eslint`, `npx tsc`, 또는 Node-based test
명령이 실패할 때는 단순히 의존성이 없다고 단정하지 말아야 한다.

실제 원인이 될 수 있는 것:
- 과도하게 길어진 `PATH`
- 중복이 많은 `PATH`
- `cmd.exe` 기반 실행에서 Node 경로가 뒤로 밀리는 문제
- npm lifecycle이 local `.bin` 경로를 앞에 추가하는 동작

현재 MStack은 Node-family subprocess에 한해 국소 mitigation을 적용한다.
하지만 이것은 머신 전체를 교정하는 것이 아니라, runtime 쪽 방어막에 가깝다.

운영 대응 권장:

1. `PATH`에서 중복된 Python, Git, Node, npm user-bin 항목 제거
2. `C:\Program Files\nodejs`가 유지되는지 확인
3. 터미널과 IDE 재시작
4. 아래 명령으로 `cmd.exe` 기준 Node 해석 확인

```text
cmd.exe /d /c "where node && where npm && node --version && npm --version"
```

참고 문서:
- Microsoft Learn: `cmd.exe` command-line and environment string limitation
- npm Docs: scripts and lifecycle `PATH` behavior
- `@npmcli/run-script`: Windows shell behavior and no `prepend-node-path`

## 실전 사용 예시

### 1. Python 프로젝트 기능 추가

```text
Use $mstack-pipeline to add CSV import end-to-end and carry it through review, QA, and ship.
```

### 2. Codex skill 수정

```text
Use $mstack-plan to define the scope and test strategy for this Codex skill update.
Then use $mstack-review to inspect the final prompt and reference changes.
```

### 3. Windows real-toolchain 문제 분석

```text
Use $mstack-investigate to find why the Windows real toolchain test fails under npm install.
Then use $mstack-qa to validate the final fix path.
```

### 4. 설치 전략 비교

```text
Use $pipeline-coordinator to compare direct install, plugin-first, and hybrid packaging strategies.
```

### 5. 배포 직전 게이트

```text
Use $mstack-review, then $mstack-qa, then $mstack-ship for this release candidate.
```

## 마무리 선택 기준

정리하면:

- 설계만: `mstack-plan`
- 원인 분석: `mstack-investigate`
- 검증만: `mstack-qa`
- 리뷰만: `mstack-review`
- 끝까지 자동 진행: `mstack-pipeline`
- 큰 의사결정 병렬화: `pipeline-coordinator`

가장 자주 쓰는 기본형:

```text
Use $mstack-pipeline to handle this request end-to-end: [task].
```
