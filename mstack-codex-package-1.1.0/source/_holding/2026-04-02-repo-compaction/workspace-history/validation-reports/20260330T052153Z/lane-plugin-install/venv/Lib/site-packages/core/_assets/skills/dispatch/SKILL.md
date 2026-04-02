---
name: mstack-dispatch
description: >
  작업 오케스트레이터 스킬. 사용자 요청을 분석하여 SINGLE/SUBAGENT/AGENT_TEAMS 모드를 자동 추천하고,
  적절한 에이전트 팀 구성(역할, 모델 믹스, 파이프라인 단계)을 결정한 뒤 실행까지 자동화한다.
  smart_route 엔진(drift.py)을 기반으로 파일 수, 모듈 간 의존성, API 계약 변경을 분석한다.
  이 스킬은 dispatch, 자동 실행, auto, orchestrate, 팀 구성, agent team, subagent,
  "알아서 해줘", "자동으로 돌려", "어떤 모드로 해야 해", "팀 추천해줘",
  "에이전트 구성", "작업 분배", delegate, "누가 뭘 해야 해" 등
  작업 자동 분배/에이전트 팀 구성/실행 위임이 필요한 모든 상황에서 반드시 사용해야 한다.
  사용자가 큰 작업을 요청하면 명시적으로 dispatch를 언급하지 않아도 이 스킬로 팀 구성을 제안하라.
  mstack SDLC 파이프라인의 전 단계에서 호출 가능한 오케스트레이터 레이어.
---

# /dispatch — 작업 오케스트레이터

> 파이프라인 위치: 모든 단계의 **진입점 오케스트레이터**

```
사용자 요청
    |
    v
[dispatch] ─── 분석 ──→ 모드 결정 ──→ 팀 구성 ──→ 자동 실행
    |                                               |
    ├── SINGLE: 직접 실행                            ├── /plan
    ├── SUBAGENT: subagent 위임                     ├── /review
    └── AGENT_TEAMS: 팀 구성 + 병렬 실행              ├── /qa
                                                    └── ...
```

## 왜 오케스트레이터가 필요한가

작업마다 최적의 실행 방식이 다르다. 파일 2개 수정은 직접 하면 되지만,
10개 모듈에 걸친 리팩터링은 Agent Teams가 3.5배 비용이 들어도 더 효율적이다.
이 판단을 사람이 매번 하는 건 낭비이므로 자동화한다.

---

## 실행 절차

### Step 1 — 작업 분석

사용자 요청에서 다음을 파악한다:

```bash
# 1. 변경 대상 파일 스캔
git diff --name-only HEAD 2>/dev/null || find . -name "*.py" -newer .git/HEAD
# 2. 모듈 간 의존성 확인
# 3. API 계약 파일 변경 여부
# 4. 작업 복잡도 평가
```

분석 결과를 표로 정리:

| 지표 | 값 |
|------|------|
| 변경 예상 파일 수 | N |
| 모듈 간 의존성 | Yes/No |
| API 계약 변경 | Yes/No |
| 예상 비용 배율 | 1.0x / 1.5x / 3.5x |

### Step 2 — 모드 결정 (smart_route 로직)

```
파일 수 < 3                              → SINGLE (직접 실행)
파일 수 < 5 AND 독립적                    → SUBAGENT (위임)
API 계약 변경 OR 모듈 간 의존성           → AGENT_TEAMS (팀)
파일 수 >= 5                             → AGENT_TEAMS (팀)
```

### Step 3 — 팀 구성 추천

#### SINGLE 모드
```markdown
## Dispatch: SINGLE
- 실행자: 현재 세션 (직접 실행)
- 비용 배율: 1.0x
- 파이프라인: 요청에 맞는 단일 스킬 호출
```

#### SUBAGENT 모드
```markdown
## Dispatch: SUBAGENT
- 리드: 현재 세션 (조율)
- 서브에이전트: 1-2개 (독립 작업 위임)
- 모델 믹스: Lead=Opus, Sub=Sonnet
- 비용 배율: ~1.5x
- 파이프라인: 리드가 /plan → 서브에이전트가 구현 → 리드가 /review
```

각 서브에이전트에게 위임할 내용:
```
Agent 1: [구체적 작업 + 담당 파일]
Agent 2: [구체적 작업 + 담당 파일]
```

#### AGENT_TEAMS 모드
```markdown
## Dispatch: AGENT_TEAMS
- 리드 (Opus): 전체 조율 + /plan + /review
- 팀원 A (Sonnet): [역할] — 담당 디렉토리
- 팀원 B (Sonnet): [역할] — 담당 디렉토리
- 팀원 C (Haiku): [보조 역할] — 테스트/문서
- 비용 배율: ~3.5x
- 파이프라인: 리드 /plan → 팀 병렬 구현 → 리드 /review → /ship → /qa
```

팀 구성 원칙:
- 리드는 항상 Opus (판단력 필요)
- 독립적인 모듈은 Sonnet 팀원에게 병렬 할당
- 테스트 생성, 문서 작성은 Haiku에게 (비용 효율)
- 공유 모듈 수정은 리드만 (mstack-careful Rule 2)

### Step 4 — 사용자 승인

추천 결과를 보여주고 승인을 받는다:

```markdown
## 추천 구성
[모드 + 팀 구성 + 예상 비용]

실행하시겠습니까?
- [ ] 승인 — 이대로 실행
- [ ] 조정 — 팀 구성 변경
- [ ] 취소 — 수동으로 진행
```

### Step 5 — 자동 파이프라인 실행

승인 후 `core/pipeline.py`의 템플릿에 따라 **전 단계를 자동 체이닝**한다.
사용자 개입은 **최초 plan 승인 1회만** 필요하며, 이후 모든 단계가 자동 실행된다.

#### 파이프라인 템플릿 (pipeline.py 기반)

| 작업 유형 | 자동 실행 순서 |
|----------|---------------|
| feature  | plan → implement → review → qa → ship → retro |
| bugfix   | investigate → implement → qa → ship → retro |
| refactor | plan → implement → review → qa → ship → retro |
| test     | qa |
| deploy   | ship → qa → retro |
| retro    | retro |

#### 자동 실행 흐름 (feature 예시)

```
1. /plan 실행 → plan.md 생성
2. 사용자 승인 대기 (최초 1회 — 유일한 개입 지점)
3. 승인 후 자동 체이닝:
   ┌─ Agent(prompt="plan.md 기반 구현. mstack-careful 준수.", model=sonnet)
   ├─ 구현 완료 → /review 자동 실행
   ├─ AUTO-FIX 발견 → 자동 수정 적용
   ├─ /qa 실행
   │   ├─ PASS → resolve_git_lock() → /ship 자동 커밋 → cost.record_session() → /retro 실행
   │   └─ FAIL → 자동 재시도 사이클 진입 ↓
   │
   │  ┌── 재시도 사이클 (최대 3회) ──┐
   │  │ /review → 원인 분석          │
   │  │ 자동 수정 적용               │
   │  │ /qa 재실행                   │
   │  │   ├─ PASS → 사이클 탈출     │
   │  │   └─ FAIL → 다음 재시도     │
   │  └─────────────────────────────┘
   │
   └─ 3회 실패 → 파이프라인 중단 + 결과 보고
4. memory.py로 세션 결과 저장 → 다음 세션에서 자동 로드
```

#### SINGLE 실행
해당 파이프라인 스킬을 직접 호출한다.
파이프라인 엔진(`execute_pipeline`)이 스테이지별로 자동 체이닝.

#### SUBAGENT 실행 (Cowork)
```
# Cowork에서: Agent 도구로 서브에이전트 생성
# pipeline.generate_dispatch_prompt()가 자동 생성한 프롬프트 사용
Agent(prompt=generate_dispatch_prompt(work_type, plan_doc), description="[역할]")
```

각 서브에이전트 프롬프트에 포함할 내용:
- 담당 파일/디렉토리 범위
- 참조할 mstack 스킬 (mstack-careful 항상 포함)
- 완료 기준 (테스트 통과, 린트 클린)
- 금지 사항 (담당 범위 외 수정 금지)
- **자동 재시도 규칙**: qa 실패 시 review→fix→qa 최대 3회

#### AGENT_TEAMS 실행 (Claude Code)
```
# Claude Code에서: Shift+Tab → 위임 모드
# CLAUDE.md에 팀 구성이 자동 주입됨
# pipeline.py가 전체 흐름 조율
```

`.claude-prompts/` 아래에 팀별 프롬프트 생성:
```
.claude-prompts/
├── 00-lead.md      ← 리드 역할 + 전체 조율 + 파이프라인 실행
├── 01-impl-a.md    ← 팀원 A 구현 지시
├── 02-impl-b.md    ← 팀원 B 구현 지시
└── 03-support.md   ← 보조 (테스트/문서)
```

### Step 6 — 결과 수집 + 메모리 저장

실행 완료 후:
1. 각 에이전트/팀원의 결과를 수집
2. 충돌 감지 (같은 파일 수정 등)
3. 통합 diff 생성
4. mstack-qa 자동 호출하여 전체 테스트
5. **memory.py에 세션 결과 자동 저장** (JSONL)

```markdown
## Dispatch 결과
- 모드: AGENT_TEAMS
- 팀원: 3명
- 소요 시간: ~Xmin
- 변경 파일: N개
- 테스트: PASS/FAIL
- 재시도: N회
- 메모리 저장: ✅
- 다음 단계: /qa 완료 → /retro 권장
```

### Step 7 — 세션 간 연속성 (memory.py 연동)

다음 세션 시작 시 자동으로:
1. `memory.load_recent(5)` — 최근 5개 세션 결과 로드
2. `memory.get_pending_tasks()` — 미완료 작업 추출
3. `memory.generate_context()` — CLAUDE.md 삽입용 요약 생성

```markdown
## 이전 세션 컨텍스트
- [2026-03-22 10:00] feature: pipeline.py 구현 — ✅ PASS (148 tests)
- [2026-03-22 11:00] refactor: hooks.py freeze — ✅ PASS (148 tests)

### 미완료 작업
- [ ] SURFACE S-1: cmd_init 장함수 분리
- [ ] SURFACE S-2: mstack.py subprocess 에러 핸들링
```

이 컨텍스트를 기반으로 dispatch가 다음 작업을 자동 추천한다.

---

## 파이프라인 연결 매트릭스

dispatch가 작업 유형에 따라 호출하는 파이프라인:

| 작업 유형 | 파이프라인 |
|----------|-----------|
| 신규 기능 | mstack-plan → 구현 → mstack-review → mstack-ship → mstack-qa |
| 버그 수정 | mstack-investigate → 수정 → mstack-qa |
| 리팩터링 | mstack-plan → 구현 → mstack-review → mstack-qa |
| 테스트 보강 | mstack-qa (회귀 테스트 자동 생성 모드) |
| 배포 | mstack-ship → mstack-qa |
| 회고 | mstack-retro |

모든 경우에 mstack-careful이 크로스커팅으로 적용된다.

## 비용 가드

smart_route의 cost_sensitive 플래그를 준수한다:
- AGENT_TEAMS 추천 시 반드시 비용 경고 표시: "~3.5x 토큰 소비"
- 사용자가 비용에 민감하면 SUBAGENT로 다운그레이드 제안
- cost.py 연동: 세션 시작/종료를 자동 기록

## mstack 파이프라인 스킬 참조
- mstack-plan → mstack-review → mstack-ship → mstack-qa → mstack-investigate → mstack-retro
- mstack-careful: 모든 단계에 적용 가능한 안전 가드레일
- mstack-dispatch (현재): 전 파이프라인 진입점 오케스트레이터
