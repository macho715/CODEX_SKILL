# System Architecture — mstack (ccat)

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Entry Points                         │
│  mstack.py (init/cost/check/upgrade/doctor)  │  ccat.py (init) │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                         core/ (13 modules)                      │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ config   │  │ types    │  │ drift    │  │ session  │       │
│  │ (preset  │  │ (enums,  │  │ (smart   │  │ (state   │       │
│  │  loader) │  │  dtypes) │  │  router) │  │  mgmt)   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ pipeline │  │ memory   │  │ hooks    │  │ skills   │       │
│  │ (auto-   │  │ (JSONL   │  │ (event   │  │ (deploy  │       │
│  │  chain)  │  │  persist)│  │  scripts)│  │  + index)│       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐      │
│  │ cost     │  │dashboard │  │ doctor   │  │ claude_md │      │
│  │ (JSONL   │  │ (Chart.js│  │ (env     │  │ (CLAUDE.md│      │
│  │  parser) │  │  HTML)   │  │  diag)   │  │  gen)     │      │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘      │
└─────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     Supporting Layers                            │
│  skills/ (8 SDLC skills)  │  presets/ (3 JSON)                  │
│  prompts/ (4 templates)   │  ci/ (GitHub Actions)               │
└─────────────────────────────────────────────────────────────────┘
```

## Module Dependency Graph

```
mstack.py ──┬── core/config.py ──── core/types.py
            ├── core/skills.py
            ├── core/hooks.py
            ├── core/claude_md.py ── core/skills.py
            ├── core/cost.py ────── core/types.py
            ├── core/dashboard.py ── core/cost.py
            ├── core/drift.py ───── core/types.py
            ├── core/session.py ──── core/types.py
            └── core/doctor.py

core/pipeline.py ── core/memory.py
                 ── core/session.py
                 ── core/drift.py
```

## Core Module Details

### types.py — 공통 데이터 타입

프로젝트 전역에서 사용하는 enum과 dataclass를 정의합니다.

- **Enums**: `Lang` (PYTHON/TYPESCRIPT/GO/RUST), `HookEvent` (4종), `HookType`, `RouterDecision` (SINGLE/SUBAGENT/AGENT_TEAMS)
- **Dataclasses**: `Preset`, `CostEntry`, `HookConfig`, `DriftItem`, `RouterResult`, `DashboardData`, `MemoryEntry`, `PipelineResult`

### config.py — 프리셋 로더

프로젝트 언어를 자동 감지하고 적절한 프리셋(test/lint/typecheck 명령어)을 로드합니다.

- `detect_lang()` — pyproject.toml, package.json, go.mod, Cargo.toml 존재 여부로 판별
- `load_preset(name)` — presets/ JSON 파일 로드, `_freeze_preset()`으로 불변 처리
- `resolve_preset()` — lang_override, preset_override 우선순위 적용
- 빌트인 폴백: Python(pytest/ruff/mypy), TypeScript(vitest/eslint/tsc), Go, Rust

### drift.py — Smart Router

파일 변경 분석 기반으로 에이전트 팀 구성을 결정합니다.

- `compute_hash(path)` — SHA256 상위 12자로 파일 해시 생성
- `detect_drift(snapshot_a, snapshot_b)` — 두 스냅샷 간 added/removed/modified 항목 탐지
- **라우팅 기준**: <3 files → SINGLE (1.0x), <5 files → SUBAGENT (1.8x), ≥5 files → AGENT_TEAMS (3.5x)
- 모듈 간 의존성, API 계약 변경도 가중치로 반영

### pipeline.py — 자동 실행 엔진

dispatch 승인 후 SDLC 파이프라인 전체를 자동으로 체이닝합니다.

- `PIPELINE_TEMPLATES` — WorkType별 스테이지 순서 정의 (feature: plan→impl→review→qa→ship→retro)
- QA 실패 시 review→fix→qa 자동 재시도 (최대 3회)
- `resolve_git_lock()` — .git/*.lock 파일 자동 해소 (Cowork 환경 호환)

### memory.py — 세션 메모리

세션 결과를 JSONL로 저장하여 다음 세션에서 컨텍스트를 자동 복원합니다.

- 저장 경로: `.claude/memory/sessions.jsonl`
- `save_session(entry)` — MemoryEntry를 JSONL 한 줄로 append
- `load_all()` — 전체 세션 로드 (blank line 무시)
- `_rotate_if_needed()` — 100 세션 초과 시 최근 100개만 유지
- `generate_context_md()` — 최근 세션 요약을 `.claude/memory/context.md`로 생성

### session.py — 세션 상태 관리

현재 세션의 RouterResult를 JSON으로 저장하고 CLAUDE.md 배너를 생성합니다.

- `write_session()` — `.claude/session.json`에 상태 저장 (TTL 30분 기본)
- `read_session()` — TTL 만료 체크 후 유효한 세션만 반환
- `patch_settings_env()` — settings.json에 환경 변수 자동 주입
- `ACTION_GUIDE` — SINGLE/SUBAGENT/AGENT_TEAMS별 사용자 안내 메시지

### hooks.py — 이벤트 훅 생성

Claude Code 훅 이벤트에 대응하는 bash 스크립트를 생성합니다.

- **이벤트**: TaskCompleted, TeammateIdle, PreToolUse, PostToolUse
- **타임아웃**: LONG=30s, MEDIUM=5s, FAST=200ms
- 훅 스크립트 → lint, test, typecheck 자동 실행

### skills.py — 스킬 배포

8개 SDLC 스킬을 `.claude/skills/mstack/`으로 배포하고 Lazy Index를 생성합니다.

- `SKILL_INDEX` — 8 스킬 메타데이터 (persona, description, triggers)
- `deploy_skills(src, target)` — 소스 디렉토리에서 SKILL.md 복사
- `generate_lazy_index()` — 토큰 절약형 인덱스 생성 (스킬명 + 트리거만)

### cost.py — 비용 추적

JSONL 형식의 비용 로그를 파싱하고 집계합니다.

- `parse_jsonl(path)` — CostEntry 리스트로 파싱 (blank line 무시)
- `aggregate(entries, by)` — model/date/session별 집계
- `format_ascii_table()` — 터미널 출력용 테이블
- `record_session()` — 현재 세션 비용 기록

### dashboard.py — 인터랙티브 대시보드

Chart.js 기반 단일 HTML 파일 대시보드를 생성합니다.

- CDN 기반, 외부 의존성 없음
- 필터: 기간, 모델
- 차트: 일별 추이(line), 모델별 비율(pie), 세션별 테이블

### claude_md.py — CLAUDE.md 생성기

프로젝트 컨텍스트 문서(CLAUDE.md)를 자동 생성합니다.

- `lazy_skills` 모드: 인덱스만 포함 (토큰 절약)
- `inline` 모드: 스킬 전문 포함 (토큰 사용 ↑)
- 훅 설명 (6 이벤트), 코딩 규칙, 구조 정보 포함

### doctor.py — 환경 진단

`mstack doctor` 명령으로 개발 환경을 점검합니다.

- `check_python()`, `check_claude_cli()`, `check_git()` 등
- `CheckResult` (name, status=PASS/WARN/FAIL, message, hint)
- `format_results()` — 프로젝트별 힌트 포함 결과 출력

## Safety Architecture

```
┌─────────────────────────────────────────────────┐
│            /careful (Cross-cutting Layer)        │
├─────────────────────────────────────────────────┤
│ • force push 금지                               │
│ • 공유 모듈 변경 경고                             │
│ • 프로덕션 직접 수정 차단 (freeze)                │
│ • 시크릿 노출 방지 (.env, credentials)           │
│ • 위험 명령어 감지 (rm -rf, git reset --hard)    │
├─────────────────────────────────────────────────┤
│ /plan → /review → /ship → /qa → /investigate    │
│                                    ↓ (fail)     │
│                              /investigate       │
│                                    ↓ (fix)      │
│                              /qa (retry ≤3)     │
└─────────────────────────────────────────────────┘
```

## Data Flow

```
사용자 요청
    ↓
/dispatch (drift.py: Smart Router)
    ↓ RouterResult
session.py: write_session() → .claude/session.json
    ↓
pipeline.py: auto_chain()
    ↓ 각 스테이지 실행
    ├── plan → review → implement → qa → ship
    ↓
memory.py: save_session() → .claude/memory/sessions.jsonl
    ↓
cost.py: record_session() → cost 로그
    ↓
dashboard.py: generate_html() → 인터랙티브 리포트
```

## Deployment Paths

| 환경 | 경로 |
|------|------|
| **Claude Code** | `.claude/commands/*.md` → `.claude/skills/mstack/*/SKILL.md` |
| **Cowork** | `skills/*/SKILL.md` → `package_skill.py` → `.skill` 패키지 → `present_files` |
| **CI** | `ci/check.py validate` / `ci/check.py drift` / `ci/check.py gen-matrix` |
