# mstack 사용자 가이드 (v1.4)

> **버전**: 1.1.0 (v1.4 빌드)
> **최종 업데이트**: 2026-03-22
> **대상 독자**: Claude Code로 팀 개발하는 모든 개발자 (초보자 포함)
> **테스트 현황**: 241 tests passed, core/ 100% coverage

---

## 목차

1. [mstack이 뭔가요?](#1-mstack이-뭔가요)
2. [설치하기](#2-설치하기)
3. [처음 시작하기 — 5분 퀵스타트](#3-처음-시작하기--5분-퀵스타트)
4. [CLI 명령어 완전 가이드](#4-cli-명령어-완전-가이드)
5. [프리셋 시스템](#5-프리셋-시스템)
6. [스킬 시스템 — 8종 SDLC 스킬](#6-스킬-시스템--8종-sdlc-스킬)
7. [파이프라인 자동 실행](#7-파이프라인-자동-실행)
8. [세션 메모리](#8-세션-메모리)
9. [훅(Hook) 시스템](#9-훅hook-시스템)
10. [Agent Teams Smart Router](#10-agent-teams-smart-router)
11. [CLAUDE.md 자동 생성](#11-claudemd-자동-생성)
12. [비용 추적과 대시보드](#12-비용-추적과-대시보드)
13. [환경 진단 — mstack doctor](#13-환경-진단--mstack-doctor)
14. [드리프트 탐지](#14-드리프트-탐지)
15. [내 프로젝트에 맞게 설정하기](#15-내-프로젝트에-맞게-설정하기)
16. [자주 묻는 질문 (FAQ)](#16-자주-묻는-질문-faq)
17. [트러블슈팅](#17-트러블슈팅)
18. [부록 — 환경변수 / NFR / 용어집](#18-부록)

---

## 1. mstack이 뭔가요?

### 한 줄 요약

**mstack**은 Claude Code에서 여러 AI 에이전트가 팀으로 협업할 때, 개발 프로세스를 자동화하는 CLI 도구입니다.

### 왜 필요한가요?

Claude Code로 코드를 작성할 때, 파일이 많아지면 혼자(SINGLE 모드)로는 한계가 있습니다. 여러 에이전트가 동시에 작업하면 빠르지만, 그만큼 비용도 늘고 관리도 복잡해집니다.

mstack은 이 문제를 해결합니다:

- **"이 작업, 혼자 할까 팀으로 할까?"** — Smart Router가 자동 판단해줍니다
- **"리뷰 → 테스트 → 배포, 순서가 맞나?"** — 파이프라인이 자동으로 체이닝합니다
- **"비용이 얼마나 들었지?"** — 대시보드에서 한눈에 확인합니다
- **"위험한 명령어를 실행하려고 해!"** — 보안 훅이 자동 차단합니다

### 주요 기능 한눈에 보기

| 기능 | 설명 | 관련 모듈 |
|------|------|-----------|
| Smart Router | 파일 수·의존성 분석 → SINGLE/SUBAGENT/AGENT_TEAMS 자동 추천 | `core/drift.py` |
| 파이프라인 | plan→구현→review→qa→ship→retro 자동 체이닝 | `core/pipeline.py` |
| 세션 메모리 | 이전 세션 결과를 다음 세션에서 자동 활용 | `core/memory.py` |
| 비용 추적 | 모델별·세션별 비용 집계 + 인터랙티브 대시보드 | `core/cost.py`, `core/dashboard.py` |
| 8종 스킬 | plan, review, ship, qa, investigate, retro, careful, dispatch | `skills/` |
| 6종 훅 | 보안 게이트, 자동 린트, 비용 로깅 등 | `core/hooks.py` |
| 환경 진단 | Python, git, Claude CLI 등 개발 환경 자동 점검 | `core/doctor.py` |

---

## 2. 설치하기

### 필요한 것

| 항목 | 최소 버전 | 확인 방법 |
|------|-----------|-----------|
| Python | 3.11+ | `python --version` |
| pip | 최신 | `pip --version` |
| Git | 2.30+ | `git --version` |
| Claude Code CLI | 최신 | `claude --version` |

### 설치 방법

**방법 1: pip로 직접 설치 (간단)**

```bash
# ccat 프로젝트 디렉토리에서
pip install -e .
```

**방법 2: setup.sh 사용**

```bash
./setup.sh
```

> `setup.sh`는 내부적으로 `python ccat.py`를 실행하는 래퍼 스크립트입니다.

### 설치 확인

```bash
# 버전 확인
mstack --version
# → mstack 1.1.0

# 환경 진단 (설치 후 꼭 한 번 실행하세요!)
mstack doctor
```

`mstack doctor` 실행 결과가 모두 PASS이면 준비 완료입니다:

```
[mstack doctor]
  ✅ Python       3.12.0 (>= 3.11 required)
  ✅ pip          24.0
  ✅ pytest       8.1.0
  ✅ Git          2.43.0
  ✅ Claude CLI   1.0.2
```

---

## 3. 처음 시작하기 — 5분 퀵스타트

### Step 1: 프로젝트 디렉토리로 이동

```bash
cd my-project
```

### Step 2: mstack 초기화

```bash
mstack init
```

이 한 줄이면 끝입니다! mstack이 자동으로:

1. 프로젝트 언어를 감지합니다 (pyproject.toml → Python, package.json → TypeScript 등)
2. 적절한 프리셋을 선택합니다
3. 다음 파일들을 생성합니다:

```
my-project/
├── CLAUDE.md                        ← AI가 프로젝트를 이해하는 컨텍스트 파일
└── .claude/
    ├── settings.json                ← 훅·권한 설정
    ├── skills/mstack/               ← 8종 스킬 파일
    │   ├── plan/SKILL.md
    │   ├── review/SKILL.md
    │   ├── ship/SKILL.md
    │   ├── qa/SKILL.md
    │   ├── investigate/SKILL.md
    │   ├── retro/SKILL.md
    │   ├── careful/SKILL.md
    │   └── dispatch/SKILL.md
    └── hooks/                       ← 자동화 스크립트
        ├── on-task-completed.sh
        └── on-teammate-idle.sh
```

### Step 3: Claude Code 실행

```bash
claude
```

이제 Claude Code 안에서 `/plan`, `/review`, `/ship` 같은 스킬을 사용할 수 있습니다!

### Step 4: 첫 작업 해보기

```
# Claude Code 대화창에서:

> 새로운 로그인 기능을 만들어줘

# mstack이 자동으로:
# 1. Smart Router가 파일 수를 분석 → SINGLE/SUBAGENT/AGENT_TEAMS 추천
# 2. /plan 스킬로 구현 계획 작성
# 3. /review로 코드 리뷰
# 4. /qa로 테스트 실행
# 5. /ship으로 커밋
```

---

## 4. CLI 명령어 완전 가이드

### 4.1 `mstack init` — 프로젝트 초기화

프로젝트에 mstack을 처음 설정할 때 사용합니다.

```bash
mstack init [옵션]
```

**사용 가능한 옵션:**

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--preset NAME` | 자동 감지 | 프리셋 이름 지정 |
| `--lang LANG` | 자동 감지 | 언어 강제 지정 (python, ts, go, rust) |
| `--hooks basic\|extended` | `basic` | 훅 수준 선택 |
| `--force` | false | 기존 파일 덮어쓰기 (백업 생성) |
| `--dry-run` | false | 실제 파일 생성 없이 계획만 출력 |
| `--no-lazy` | false | 스킬 전문을 CLAUDE.md에 직접 포함 |

**자주 쓰는 예시:**

```bash
# 가장 기본적인 초기화 (대부분 이것으로 충분)
mstack init

# Python 프로젝트로 강제 지정 + 보안 훅 포함
mstack init --lang python --hooks extended

# HVDC 프로젝트 전용 설정
mstack init --preset hvdc --hooks extended

# 이미 초기화된 프로젝트를 최신 설정으로 업데이트
mstack init --force

# 어떤 파일이 생성될지 미리 보기 (파일 생성 안 함)
mstack init --dry-run
```

**출력 예시:**

```
[mstack] Detected language: python
[mstack] Using preset: python
[mstack] ✅ Skills: 8 files → .claude/skills/mstack/
[mstack] ✅ Hooks: 2 files → .claude/hooks/
[mstack] ✅ settings.json → .claude/settings.json
[mstack] ✅ CLAUDE.md → CLAUDE.md (~1240 tokens)
[mstack] 🎉 Init complete! Run `claude` to start.
```

---

### 4.2 `mstack cost` — 비용 조회

Claude Code 사용 비용을 확인합니다.

```bash
mstack cost [옵션]
```

| 옵션 | 설명 |
|------|------|
| `--dashboard` | Chart.js HTML 대시보드 생성 |
| `--threshold USD` | 비용 임계값 (초과 시 GitHub Issue 알림) |
| `--output PATH` | 대시보드 저장 경로 |
| `--no-open` | 브라우저 자동 열기 비활성화 |

```bash
# 터미널에서 비용 요약 보기
mstack cost

# 웹 대시보드로 보기 (브라우저 자동 열림)
mstack cost --dashboard

# 비용이 $10 넘으면 GitHub Issue 자동 생성
mstack cost --threshold 10.0

# 대시보드를 파일로만 저장
mstack cost --dashboard --output ./reports/cost.html --no-open
```

**터미널 출력 예시:**

```
┌─────────────────────────────────────┐
│ mstack Cost Report                  │
├──────────────┬──────────────────────┤
│ Period       │ 2026-03-01~2026-03-22│
│ Total Cost   │ $3.47                │
│ Sessions     │ 42                   │
│ Avg/Session  │ $0.08                │
├──────────────┴──────────────────────┤
│ By Model                            │
│  sonnet-4    │ $2.10 (61%)          │
│  opus-4      │ $1.37 (39%)          │
└─────────────────────────────────────┘
```

---

### 4.3 `mstack check` — 작업 모드 추천

변경된 파일을 분석해서 어떤 모드로 작업할지 추천해줍니다.

```bash
mstack check [--files FILE...]
```

```bash
# git 변경 파일 자동 감지
mstack check

# 특정 파일로 분석
mstack check --files src/main.py tests/test_main.py
```

**출력 예시:**

```
👥 Recommendation: AGENT_TEAMS
  Files: 5
  Reason: Cross-module coordination needed (⚠ ~3.5x tokens)
  Action: Shift+Tab 으로 위임 모드로 전환하세요
```

---

### 4.4 `mstack doctor` — 환경 진단

개발 환경이 제대로 설정되었는지 점검합니다.

```bash
mstack doctor
```

**점검 항목:**

| 항목 | 필수 | 기준 |
|------|------|------|
| Python | ✅ | 3.11 이상 |
| pip | ✅ | 설치 확인 |
| pytest | ⚠️ | 설치 권장 |
| Git | ✅ | 설치 확인 |
| Claude CLI | ✅ | 설치 확인 |
| 코드 포매터 | ⚠️ | ruff/flake8 등 |

**결과 상태:**

| 상태 | 의미 |
|------|------|
| ✅ PASS | 정상 |
| ⚠️ WARN | 작동은 하지만 권장사항 미충족 |
| ❌ FAIL | 필수 요건 미충족 — 설치/수정 필요 |

```
[mstack doctor]
  ✅ Python       3.12.0
  ✅ pip          24.0
  ⚠️ pytest       not found — install with: pip install pytest
  ✅ Git          2.43.0
  ❌ Claude CLI   not found — install from: https://claude.ai/download
```

---

### 4.5 `mstack upgrade` — 업그레이드

```bash
# 현재 버전 확인만
mstack upgrade --check-only

# 최신 버전으로 업그레이드
mstack upgrade
```

---

## 5. 프리셋 시스템

프리셋은 "언어별 기본 설정 묶음"입니다. 테스트 명령어, 린트 도구, 타입 체크 도구 등이 포함됩니다.

### 내장 프리셋

| 프리셋 | 언어 | 테스트 명령어 | 린트 | 타입 체크 |
|--------|------|--------------|------|-----------|
| `python` | Python | `pytest tests/ -x` | `ruff check .` | `mypy --strict .` |
| `ts` | TypeScript | vitest | eslint | tsc |
| `go` | Go | go test | golangci-lint | (내장) |
| `rust` | Rust | cargo test | clippy | (내장) |
| `hvdc` | Python | `pytest tests/ -x --tb=short` | `ruff check .` | `mypy --strict .` |
| `minimal` | 미지정 | — | — | — |

### 언어 자동 감지

mstack은 프로젝트 루트의 파일을 보고 언어를 자동으로 판단합니다:

| 이 파일이 있으면 | 이 언어로 감지 |
|-----------------|---------------|
| `pyproject.toml`, `requirements.txt`, `setup.py` | Python |
| `package.json`, `tsconfig.json` | TypeScript |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| (아무것도 없으면) | Unknown → minimal 프리셋 |

### 커스텀 프리셋 만들기

`presets/` 디렉토리에 JSON 파일을 추가하면 됩니다:

```json
{
  "name": "my-team",
  "lang": "python",
  "test_cmd": "pytest tests/ -v --cov=src",
  "lint_cmd": "ruff check . --fix",
  "type_cmd": "pyright",
  "rules": [
    "항상 타입 힌트 사용",
    "함수는 50줄 이하로 유지",
    "docstring 필수"
  ],
  "permissions": {
    "Bash": true,
    "Edit": true,
    "Write": true,
    "Read": true
  }
}
```

사용:

```bash
mstack init --preset my-team
```

---

## 6. 스킬 시스템 — 8종 SDLC 스킬

스킬은 Claude Code 안에서 특정 작업을 수행하는 "전문가 모드"입니다. `/plan`이라고 입력하면 plan 스킬이 활성화되어 구현 계획을 작성합니다.

### SDLC 파이프라인 흐름

```
  ① /plan ──→ ② /review ──→ ③ /ship ──→ ④ /qa
                                           │
                                      실패 시 ↓
                                    ⑤ /investigate
                                           │
                                      해결 후 ↓
                                      ④ /qa (재시도)
                                           │
                                      통과 시 ↓
                                    ⑥ /retro

  ⚡ /dispatch ── 전체 파이프라인 자동 오케스트레이션
  🛡️ /careful ── 모든 단계에 안전 가드레일 적용
```

### 각 스킬 상세 설명

#### ① `/plan` — 구현 계획 수립

**언제 사용?** 새 기능을 만들거나, 대규모 리팩터링을 시작할 때

**무엇을 하나?** 2-Phase 구현 계획을 작성합니다:

- **Phase 1 (CEO Review)**: 비즈니스 임팩트, 리스크, 우선순위를 한 페이지로 정리
- **Phase 2 (Eng Review)**: 변경할 파일 목록, 의존성, Mermaid 아키텍처 다이어그램, 테스트 전략

**사용 예시:**

```
> /plan 사용자 로그인 기능 구현

[plan 스킬이 활성화됩니다]
→ Phase 1: 비즈니스 분석
→ Phase 2: 파일 변경 계획 + 아키텍처 다이어그램
→ 파일명 충돌 체크포인트 (같은 이름의 파일이 이미 있는지 확인)
```

> **Tip**: plan이 생성한 계획은 /review에서 참고됩니다. 꼭 먼저 실행하세요!

---

#### ② `/review` — 코드 리뷰

**언제 사용?** 코드를 작성한 후, 커밋하기 전에

**무엇을 하나?** 변경사항을 두 가지로 분류합니다:

| 분류 | 의미 | 처리 |
|------|------|------|
| **AUTO-FIX** | 자동으로 수정 가능한 문제 | mstack이 즉시 수정 |
| **SURFACE** | 사람의 판단이 필요한 문제 | 사용자에게 보고만 함 |

**검사 항목:**

- 보안 취약점 (하드코딩된 비밀번호, SQL injection 등)
- 성능 이슈 (불필요한 루프, N+1 쿼리 등)
- 코드 품질 (타입 힌트 누락, bare except 사용 등)
- 완전성 갭 (누락된 테스트, 미처리 엣지 케이스)

---

#### ③ `/ship` — 배포 준비

**언제 사용?** 코드 리뷰를 마치고 커밋/배포할 때

**무엇을 하나?** 배포 전 체크리스트를 실행합니다:

1. 테스트 부트스트랩 — 전체 테스트 실행
2. 커버리지 감사 — 커버리지 하락 여부 확인
3. 커밋 메시지 검증 — Conventional Commits 형식 확인
4. 브랜치 전략 점검 — force push 금지 강제

```
> /ship — 커밋 실행

[ship 스킬이 활성화됩니다]
→ pytest 실행: 241 tests passed ✅
→ 커버리지: 100% (하락 없음) ✅
→ 커밋 메시지: feat(v1.4): ... ✅
→ git commit + push 실행
```

> **중요**: `/ship`은 force push를 절대 허용하지 않습니다.

---

#### ④ `/qa` — QA 검증

**언제 사용?** 배포 후 또는 독립적으로 품질 검증할 때

**3가지 모드:**

| 모드 | 설명 | 사용 시점 |
|------|------|-----------|
| **Diff-aware** | 변경된 파일 관련 테스트만 실행 | 빠른 검증 |
| **Full** | 전체 테스트 실행 | 릴리스 전 |
| **Quick** | 스모크 테스트만 | 긴급 확인 |

**자동 회귀 테스트 생성**: 버그를 수정하면 해당 버그에 대한 회귀 테스트를 자동으로 생성합니다.

---

#### ⑤ `/investigate` — 버그 조사

**언제 사용?** 테스트가 실패하거나 버그를 발견했을 때

**작동 방식:**

1. **가설 3개 수립** — 가능한 원인을 3개 제시
2. **각 가설 검증** — 코드 읽기, 로그 분석, 재현 시도
3. **결론 도출** — 근본 원인 확정

> **핵심 규칙**: `/investigate`는 **읽기 전용(freeze)** 모드입니다. 사용자가 승인하기 전까지 프로덕션 코드를 **절대 수정하지 않습니다.**

```
> /investigate — 테스트 3개가 실패하는 원인 분석

[investigate 스킬이 활성화됩니다]
→ 가설 1: import 순서 문제 → ❌ 아님
→ 가설 2: mock 패치 범위 오류 → ✅ 확인됨!
→ 가설 3: fixture teardown 누락 → ❌ 아님
→ 결론: core.pipeline.os.rename mock이 잘못된 모듈을 패치하고 있었음
→ 수정 제안: [사용자 승인 대기]
```

---

#### ⑥ `/retro` — 회고

**언제 사용?** 기능 구현이나 버그 수정을 마쳤을 때

**무엇을 하나?** Keep/Improve/Learn 프레임워크로 회고를 작성합니다:

- **Keep** (계속할 것): 잘 된 점
- **Improve** (개선할 것): 아쉬운 점
- **Learn** (배운 것): 새로 알게 된 점

추가로 `cost.py` 비용 데이터를 자동 포함하여 비용 효율성도 분석합니다.

---

#### ⑦ `/careful` — 안전 가드레일

**언제 사용?** 자동으로 모든 단계에 적용됩니다 (별도 호출 불필요)

**5가지 안전 규칙:**

| # | 규칙 | 차단 대상 |
|---|------|-----------|
| 1 | Force Push 차단 | `git push --force`, `git push -f` |
| 2 | 공유 모듈 변경 경고 | `src/shared/`, `lib/common/`, `utils/`, `types/` 변경 시 |
| 3 | 프로덕션 Freeze | `/investigate` 중 `src/lib/app/` 수정 차단 |
| 4 | 시크릿 노출 방지 | API 키, .env 파일, 비밀번호 패턴 감지 |
| 5 | 위험 명령어 감지 | `rm -rf /`, `DROP TABLE`, `chmod 777 /` 등 |

---

#### ⑧ `/dispatch` — 작업 오케스트레이터

**언제 사용?** 다음에 무슨 작업을 할지 모를 때, 또는 작업 전체를 자동으로 돌리고 싶을 때

**무엇을 하나?**

1. 사용자 요청을 분석합니다
2. `drift.py`의 smart_route 엔진으로 파일 수/의존성/API 변경을 분석합니다
3. SINGLE / SUBAGENT / AGENT_TEAMS 모드를 자동 추천합니다
4. 승인하면 파이프라인을 자동 실행합니다

```
> /dispatch — 다음 작업 추천

[dispatch 스킬이 활성화됩니다]
→ 분석: 변경 예상 파일 3개, cross-module 의존성 없음
→ 추천: SINGLE (1.0x 비용)
→ 세부 작업: AI-1. test_session.py 커버리지 100% 달성
→ 승인하시겠습니까? [Y/n]
```

---

## 7. 파이프라인 자동 실행

### 파이프라인이 뭔가요?

파이프라인은 여러 스킬을 순서대로 자동 실행하는 체인입니다. `/dispatch`에서 승인하면 전체 흐름이 자동으로 진행됩니다.

### 작업 유형별 파이프라인

| WorkType | 스테이지 순서 |
|----------|--------------|
| FEATURE (새 기능) | plan → implement → review → qa → ship → retro |
| BUGFIX (버그 수정) | investigate → implement → review → qa → ship |
| REFACTOR (리팩터링) | plan → implement → review → qa → ship |
| TEST (테스트 추가) | implement → qa → ship |
| DEPLOY (배포) | ship |
| RETRO (회고) | retro |

### QA 실패 시 자동 재시도

QA에서 테스트가 실패하면:

```
qa (FAIL) → review → fix → qa (재시도)
```

이 사이클은 **최대 3회**까지 자동 반복됩니다. 3회 실패하면 사용자에게 보고합니다.

### Git Lock 자동 해소

Cowork 환경에서는 `.git/index.lock`이나 `.git/HEAD.lock`이 남아있어 커밋이 실패하는 경우가 있습니다. `pipeline.py`의 `resolve_git_lock()` 함수가 이를 자동으로 해소합니다:

```
.git/index.lock → .git/index.lock.bak (자동 이름 변경)
.git/HEAD.lock  → .git/HEAD.lock.bak
```

---

## 8. 세션 메모리

### 세션 메모리가 뭔가요?

Claude Code 세션이 끝나면 작업 내용이 사라집니다. 세션 메모리는 이전 세션의 결과를 저장해서 다음 세션에서 자동으로 활용할 수 있게 합니다.

### 저장 위치

| 파일 | 역할 |
|------|------|
| `.claude/memory/sessions.jsonl` | 전체 세션 기록 (JSONL, 1줄 = 1세션) |
| `.claude/memory/context.md` | 최근 10개 세션 요약 (CLAUDE.md에 삽입용) |

### 자동 로테이션

세션이 100개를 초과하면 가장 오래된 세션부터 자동 삭제됩니다. 항상 최근 100개만 유지합니다.

### 세션 상태 관리

현재 세션의 상태는 `.claude/session.json`에 저장됩니다:

```json
{
  "decision": "AGENT_TEAMS",
  "file_count": 15,
  "cost_ratio": 3.5,
  "expires_at": "2026-03-22T15:30:00Z"
}
```

- **TTL (Time-To-Live)**: 기본 30분. 만료되면 자동으로 무효화됩니다.
- 세션 시작 시 CLAUDE.md 상단에 배너가 자동 생성됩니다:

```markdown
> 👥 **Session Mode: AGENT_TEAMS** | 15 files | cost 3.5x
> Action: **Shift+Tab** 으로 위임 모드로 전환하세요.
```

---

## 9. 훅(Hook) 시스템

### 훅이 뭔가요?

훅은 "특정 이벤트가 발생하면 자동으로 실행되는 스크립트"입니다. 예를 들어, 작업이 끝나면 자동으로 린트+테스트를 실행하거나, 위험한 명령어를 실행하려고 하면 자동으로 차단합니다.

### Basic 훅 (2종) — 기본 제공

`mstack init`만 하면 자동으로 설치됩니다.

| 이벤트 | 타임아웃 | 동작 |
|--------|---------|------|
| **TaskCompleted** | 30초 | 작업 완료 후 자동으로 린트 + 테스트 실행 |
| **TeammateIdle** | 5초 | 팀원이 대기 중일 때 다음 작업 안내 출력 |

### Extended 훅 (6종) — `--hooks extended` 필요

보안 게이트, 비용 로깅 등 고급 기능이 포함됩니다.

| 이벤트 | 타임아웃 | 동작 |
|--------|---------|------|
| **TaskCompleted** | 30초 | 린트 + 테스트 자동 실행 |
| **TeammateIdle** | 5초 | 다음 작업 안내 |
| **PreToolUse** | 200ms | 🛡️ **보안 게이트** — 위험 명령 차단 |
| **PostToolUse** | 5초 | Write/Edit 후 자동 포맷 |
| **Stop** | 5초 | 세션 종료 시 비용 기록 |
| **SubagentStop** | 5초 | 서브에이전트 종료 시 비용 기록 |

### PreToolUse 보안 게이트 — 차단 패턴

PreToolUse 훅은 Claude Code가 도구를 실행하기 **직전에** 명령어를 검사합니다:

| 범주 | 차단되는 명령어 | 왜 위험한가 |
|------|----------------|-------------|
| 파일 삭제 | `rm -rf /`, `rm -rf ~` | 전체 시스템/홈 디렉토리 삭제 |
| Git 파괴 | `git push --force main` | 원격 히스토리 덮어쓰기 |
| Git 초기화 | `git reset --hard`, `git clean -fd` | 로컬 변경사항 전체 삭제 |
| DB 파괴 | `DROP TABLE`, `DROP DATABASE` | 데이터베이스 삭제 |
| 시스템 파괴 | 포크 폭탄, `mkfs`, `dd if=` | 시스템 마비/디스크 포맷 |
| 원격 실행 | `curl ... \| bash` | 검증되지 않은 스크립트 실행 |
| 권한 파괴 | `chmod -R 777 /` | 전체 시스템 권한 해제 |

차단 시 `~/.claude/cost-logs/cost.jsonl`에 보안 이벤트가 기록됩니다.

### Extended 훅 설치 방법

```bash
# 처음 설치
mstack init --hooks extended

# 이미 basic으로 설치했다면
mstack init --hooks extended --force
```

---

## 10. Agent Teams Smart Router

### 개념

"이 작업을 혼자(SINGLE) 할까, 서브에이전트(SUBAGENT)에게 맡길까, 팀(AGENT_TEAMS)으로 할까?"를 자동으로 판단하는 엔진입니다.

### 의사결정 트리

```
변경 파일 수를 센다
     │
     ├─ 1~2개 → 👤 SINGLE
     │          비용: 1.0x
     │          "혼자서 충분해요"
     │
     ├─ 3~4개 + 의존성 없음 → 🔀 SUBAGENT
     │          비용: 1.8x
     │          "서브에이전트에게 맡기세요"
     │
     ├─ 3~4개 + 의존성 있음 → 👥 AGENT_TEAMS
     │          비용: 3.5x
     │          "팀으로 협업하세요"
     │
     └─ 5개 이상 → 👥 AGENT_TEAMS
                비용: 3.5x
                "팀으로 협업하세요"
```

### "의존성"이란?

**Cross-module 의존성**: 변경 파일이 2개 이상의 최상위 디렉토리에 걸쳐 있을 때

```
src/main.py + tests/test_main.py  → ✅ cross-module (서로 다른 디렉토리)
src/main.py + src/utils.py        → ❌ 같은 디렉토리 (cross-module 아님)
```

**API Contract 변경**: 파일명에 다음 키워드가 포함될 때

```
types, schema, interface, api, contract, proto, openapi
```

예: `core/types.py` 수정 → API contract 변경으로 판단 → AGENT_TEAMS 추천

### 비용 비교

| 모드 | 토큰 비용 | 설명 |
|------|-----------|------|
| SINGLE | 1.0x | 일반 세션, 가장 저렴 |
| SUBAGENT | 1.8x | 서브에이전트가 결과 요약만 부모에게 반환 |
| AGENT_TEAMS | 3.5x | 각 팀원이 독립 컨텍스트 보유, 가장 비쌈 |

> **Tip**: 비용이 걱정된다면 `mstack check --files`로 특정 파일만 지정해서 분석해보세요.

---

## 11. CLAUDE.md 자동 생성

### CLAUDE.md란?

CLAUDE.md는 Claude Code가 프로젝트를 이해하기 위해 읽는 "컨텍스트 문서"입니다. mstack이 자동으로 생성하고 관리합니다.

### 생성되는 내용

```markdown
# 프로젝트명

## Project Structure
Language: python
Directories: src, tests, docs

## Commands
- Test: `pytest tests/ -x`
- Lint: `ruff check .`
- Type check: `mypy --strict .`

## Rules
- 항상 타입 힌트 사용
- bare except 금지

## Available Skills (Lazy Index)
| Skill | Trigger | Description |
...

## Agent Teams Routing
...

## Hooks
...

## Compaction Rules
...
```

### Lazy Index vs Inline 모드

| 모드 | CLAUDE.md 크기 | 설명 |
|------|---------------|------|
| **Lazy Index** (기본) | ~1,200 토큰 | 스킬 요약 테이블만 포함. 실제 스킬은 트리거 시 로드 |
| **Inline** | ~3,500 토큰 | 스킬 전문 포함. 토큰 소비 ↑ |

```bash
# Lazy Index (기본, 권장)
mstack init

# Inline (스킬 전문 포함)
mstack init --no-lazy
```

### Compaction Rules

Claude Code가 컨텍스트를 자동 압축할 때 **반드시 보존할 항목**:

1. 프로젝트 명령어 (test/lint/type)
2. 현재 수정 중인 파일 목록
3. 현재 작업 목표
4. KPI 목표
5. 스킬 트리거 목록
6. 보안 규칙

---

## 12. 비용 추적과 대시보드

### 데이터 수집 방법

Extended 훅(Stop/SubagentStop)이 활성화되면, 세션이 끝날 때마다 자동으로 기록됩니다.

**저장 경로**: `~/.claude/cost-logs/cost.jsonl`

**데이터 형식** (한 줄 = 한 세션):

```json
{
  "session_id": "sess-001",
  "timestamp": "2026-03-22T10:00:00Z",
  "model": "sonnet-4",
  "input_tokens": 15000,
  "output_tokens": 5000,
  "cost_usd": 0.08,
  "duration_sec": 142,
  "event_type": "session"
}
```

### HTML 대시보드

`mstack cost --dashboard`로 생성되는 대시보드 구성:

| 차트 | 내용 |
|------|------|
| Summary Cards | 총 비용, 세션 수, 세션당 평균 비용 |
| Line Chart | 일별 비용 추이 |
| Pie Chart | 모델별 비용 비율 (sonnet vs opus 등) |
| Table | 세션별 상세 내역 |

대시보드는 단일 HTML 파일로, Chart.js CDN을 사용하므로 별도 서버가 필요 없습니다.

### 비용 알림

```bash
# $10 초과 시 GitHub Issue 자동 생성
mstack cost --threshold 10.0
```

GitHub Issue 생성에는 `gh` CLI가 필요합니다. `gh`가 없거나 인증 실패 시 알림 없이 계속 진행됩니다.

---

## 13. 환경 진단 — mstack doctor

`mstack doctor`는 프로젝트 개발 환경이 올바르게 설정되었는지 자동으로 점검합니다.

### 점검 항목 상세

| 항목 | 점검 내용 | PASS 기준 | FAIL 시 해결 방법 |
|------|-----------|-----------|-------------------|
| Python | 버전 확인 | ≥ 3.11 | `pyenv install 3.12` |
| pip | 설치 확인 | 설치됨 | `python -m ensurepip` |
| pytest | 설치 확인 | 설치됨 | `pip install pytest` |
| Git | 설치 확인 | 설치됨 | OS별 패키지 관리자 사용 |
| Claude CLI | 설치 + 버전 | 설치됨 | [다운로드](https://claude.ai/download) |
| Formatter | ruff/flake8 등 | 설치됨 | `pip install ruff` |

### 프로젝트별 힌트

doctor는 프로젝트 상태에 따라 맞춤 힌트를 제공합니다:

```
[mstack doctor]
  ✅ Python       3.12.0
  ✅ Git          2.43.0
  ⚠️ pytest       not found
     Hint: This project uses pytest. Install with: pip install pytest
```

---

## 14. 드리프트 탐지

### 드리프트란?

mstack이 생성한 파일(CLAUDE.md, 스킬, 훅)이 누군가에 의해 수동으로 변경된 상태를 "드리프트"라고 합니다.

### 탐지 방법

SHA256 해시의 상위 12자를 비교합니다:

```python
from core.drift import compute_hash
hash_value = compute_hash("CLAUDE.md")
# → "a1b2c3d4e5f6"
```

### 드리프트 상태

| 상태 | 의미 |
|------|------|
| `ok` | 해시 일치 — 원본 그대로 |
| `modified` | 해시 불일치 — 수동 수정됨 |
| `missing` | 파일 삭제됨 |

### CI에서 사용하기

```bash
# CLAUDE.md + 스킬 + 훅의 드리프트 확인
python ci/check.py drift
```

---

## 15. 내 프로젝트에 맞게 설정하기

### 훅 커스터마이징

`.claude/hooks/` 디렉토리의 bash 파일을 직접 수정할 수 있습니다:

```bash
# PreToolUse 훅에 차단 패턴 추가
vim .claude/hooks/pre-tool-use.sh
```

> `mstack init --force`를 실행하면 원본으로 복구됩니다.

### 스킬 커스터마이징

`.claude/skills/mstack/*/SKILL.md` 파일을 편집하면 스킬 동작을 변경할 수 있습니다:

```bash
# review 스킬에 추가 규칙 작성
vim .claude/skills/mstack/review/SKILL.md
```

### 새 프리셋 추가

```bash
# presets/ 디렉토리에 JSON 파일 추가
vim presets/my-custom.json

# 적용
mstack init --preset my-custom
```

### CLAUDE.md 수동 수정

CLAUDE.md를 직접 편집해도 됩니다. 단, `mstack init --force`를 실행하면 덮어써집니다.

---

## 16. 자주 묻는 질문 (FAQ)

### Q: mstack init을 여러 번 실행해도 괜찮나요?

A: 네, 괜찮습니다. 이미 파일이 있으면 건너뜁니다. `--force` 옵션을 주면 기존 파일을 `.bak`으로 백업 후 덮어씁니다.

### Q: SINGLE, SUBAGENT, AGENT_TEAMS 차이가 뭔가요?

A: 비용과 속도의 트레이드오프입니다:

| 모드 | 에이전트 수 | 비용 | 속도 | 적합한 작업 |
|------|------------|------|------|------------|
| SINGLE | 1개 | 1.0x | 보통 | 파일 1~2개 수정 |
| SUBAGENT | 1+N | 1.8x | 빠름 | 독립적인 파일 3~4개 |
| AGENT_TEAMS | 팀 | 3.5x | 가장 빠름 | 복잡한 다모듈 작업 |

### Q: 비용 데이터가 안 쌓여요

A: Extended 훅이 필요합니다. `mstack init --hooks extended --force`로 재설치하세요.

### Q: Windows에서도 사용할 수 있나요?

A: CLI 자체는 작동하지만, bash 기반 훅(특히 PreToolUse 보안 게이트)은 Git Bash가 필요합니다.

### Q: 기존 프로젝트에 적용해도 코드가 변경되나요?

A: 아닙니다. mstack은 `.claude/` 디렉토리와 `CLAUDE.md`만 생성합니다. 기존 소스 코드에는 영향을 주지 않습니다.

### Q: Agent Teams 비용이 3.5x라면 너무 비싸지 않나요?

A: 파일이 많은 작업에서는 오히려 효율적입니다. SINGLE로 5개 파일을 수정하면 컨텍스트 스위칭 비용이 발생하지만, AGENT_TEAMS는 병렬 처리로 시간을 절약합니다. `mstack check`로 미리 확인하고, 정말 필요할 때만 사용하세요.

### Q: 스킬 순서를 꼭 지켜야 하나요?

A: `/dispatch`를 사용하면 자동으로 적절한 순서가 적용됩니다. 수동으로 사용할 때는 `plan → review → ship → qa` 순서를 권장하지만, 상황에 따라 개별 스킬만 사용해도 됩니다.

---

## 17. 트러블슈팅

### 문제: mstack init 후 스킬이 안 보임

**확인 방법:**

```bash
# 1. 스킬 디렉토리 존재 확인
ls .claude/skills/mstack/

# 2. CLAUDE.md에 Lazy Index 확인
grep "Available Skills" CLAUDE.md
```

**해결:**

```bash
mstack init --force
```

---

### 문제: Git 커밋이 "index.lock" 오류로 실패

**원인**: Cowork 환경에서 .git/index.lock 파일이 남아있음

**해결 (자동)**: `pipeline.py`의 `resolve_git_lock()`이 자동 처리

**해결 (수동)**:

```bash
mv .git/index.lock .git/index.lock.bak
mv .git/HEAD.lock .git/HEAD.lock.bak   # HEAD.lock도 있다면
```

---

### 문제: cost.jsonl 데이터가 비어있음

**원인**: Basic 훅에는 Stop/SubagentStop 훅이 없음

**해결:**

```bash
mstack init --hooks extended --force
```

---

### 문제: Windows에서 훅이 실행 안 됨

**원인**: Unix bash 스크립트는 Windows에서 직접 실행 불가

**해결:**

1. Git Bash 설치 (https://gitforwindows.org)
2. 또는 WSL2 환경에서 실행

---

### 문제: `mstack check`가 AGENT_TEAMS를 너무 자주 추천

**원인**: git diff가 많은 파일을 반환하고 있을 수 있음

**해결:**

```bash
# 파일을 명시적으로 지정
mstack check --files src/main.py src/utils.py
```

---

### 문제: `gh` CLI 오류로 GitHub Issue 생성 실패

**확인:**

```bash
gh auth status
```

**해결:**

```bash
gh auth login
```

---

### 문제: CLAUDE.md 토큰이 너무 많음

**원인**: Inline 모드(`--no-lazy`)로 생성했을 수 있음

**해결:**

```bash
mstack init --force    # Lazy Index 기본 모드로 재생성
```

---

## 18. 부록

### 환경변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | Agent Teams 활성화 | `1` (settings.json에 자동 설정) |
| `MSTACK_PRESET` | 현재 프리셋 이름 | 자동 감지 결과 |
| `MSTACK_HOOK_RUNNING` | PostToolUse 훅 재귀 방지 | 미설정 |

### NFR (Non-Functional Requirements)

| 항목 | 목표값 | 현재 상태 |
|------|--------|-----------|
| CLAUDE.md 토큰 | ≤ 27,000 | ✅ ~1,240 (Lazy) |
| Lazy Index 토큰 절감 | ≥ 30% | ✅ ~40% |
| PreToolUse 타임아웃 | 200ms | ✅ |
| core/ 테스트 커버리지 | ≥ 99% | ✅ 100% |
| 전체 테스트 | 통과 | ✅ 241 passed, 1 skipped |

### 용어집

| 용어 | 설명 |
|------|------|
| **SINGLE** | 하나의 Claude Code 세션으로 작업하는 모드 |
| **SUBAGENT** | 메인 에이전트가 서브에이전트에게 일부 작업을 위임하는 모드 |
| **AGENT_TEAMS** | 여러 에이전트가 팀으로 병렬 작업하는 모드 |
| **Smart Router** | 변경 파일 분석 기반 작업 모드 자동 추천 엔진 |
| **Drift** | mstack이 생성한 파일이 수동으로 변경된 상태 |
| **Compaction** | Claude Code가 긴 대화를 요약·압축하는 과정 |
| **Lazy Index** | CLAUDE.md에 스킬 요약만 포함하는 토큰 절약 모드 |
| **Hook** | 특정 이벤트에 자동 반응하는 bash 스크립트 |
| **TTL** | Time-To-Live, 세션 상태 유효 시간 (기본 30분) |
| **JSONL** | JSON Lines, 한 줄에 하나의 JSON 객체 형식 |
| **DXA** | 문서 측정 단위 (1440 DXA = 1 inch) |
| **WorkType** | 파이프라인 작업 유형 (FEATURE, BUGFIX, REFACTOR 등) |

### 프로젝트 버전 이력

| 버전 | 날짜 | 주요 변경 |
|------|------|-----------|
| v0.0 | 2026-03-22 | 프로젝트 초기화 (ccat.py + core/ 11모듈) |
| v0.2 | 2026-03-22 | AUTO-FIX 6건 + test_types.py 16 tests |
| v1.0 | 2026-03-22 | pipeline + memory 엔진 추가 |
| v1.1 | 2026-03-22 | resolve_git_lock + cost record_session |
| v1.2 | 2026-03-22 | pipeline 100% + dashboard 100% coverage |
| v1.3 | 2026-03-22 | session 100% + doctor 100% coverage |
| v1.4 | 2026-03-22 | **core/ 100% coverage** (863 stmts, 0 miss, 13/13 modules) |

---

> 이 가이드에 대한 피드백이나 질문은 프로젝트 이슈로 등록해주세요.
