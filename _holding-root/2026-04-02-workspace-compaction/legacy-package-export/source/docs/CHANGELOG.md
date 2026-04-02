# Changelog — mstack (ccat)

All notable changes to this project are documented in this file.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [1.1.0] — 2026-03-22

### Overview

프로젝트 초기화부터 core/ 100% 커버리지 달성까지의 전체 개발 이력.
총 8 커밋, 241 테스트, 13 모듈 0 miss.

---

### v1.4 — `test(v1.4): core/ 100% coverage — all 13 modules at 0 miss`

**Date**: 2026-03-22 20:31 (UTC+4)

#### Added
- `tests/test_config.py` — `load_preset` unknown preset, `resolve_preset` lang override 테스트 2건
- `tests/test_cost_core.py` — `parse_jsonl` blank line skip 테스트 1건
- `tests/test_memory.py` — `load_all` blank line skip, `_rotate_if_needed` missing file 테스트 2건
- `tests/test_skills.py` — `deploy_skills` missing source FileNotFoundError 테스트 1건

#### Changed
- `CLAUDE.md` — 커버리지 기준 섹션 추가 (≥99%, 신규 100%, 하락 금지)

#### Metrics
- 241 tests passed, 1 skipped
- core/ 100% coverage (863 stmts, 0 miss, 13/13 modules)

---

### v1.3 — `test(v1.3): session 100% + doctor 100% coverage`

**Date**: 2026-03-22 20:11 (UTC+4)

#### Added
- `tests/test_session.py` — corrupt JSON, expired TTL, invalid format, settings corrupt JSON 테스트 4건
- `tests/test_doctor.py` — `_run_cmd` FileNotFound/Timeout, `check_python` mock, `check_claude_cli` fail, `format_results` hint/plural 테스트 6건

#### Metrics
- 235 tests passed
- session.py: 90% → 100%
- doctor.py: 95% → 100%

---

### v1.2 — `test(v1.2): pipeline 100% + dashboard 100% coverage, plan checkpoint`

**Date**: 2026-03-22 19:58 (UTC+4)

#### Added
- `tests/test_pipeline.py` — `resolve_git_lock` default git_dir, OSError, partial resolution 테스트 3건
- `tests/test_dashboard.py` — 신규 파일, browser open/error, GitHub threshold success/fail/not-found/timeout 테스트 6건
- `skills/plan/SKILL.md` — 파일명 충돌 체크포인트 추가

#### Metrics
- 225 tests passed
- pipeline.py: 95% → 100%
- dashboard.py: 76% → 100%

---

### v1.1 — `feat(v1.1): resolve_git_lock + cost.py record_session`

**Date**: 2026-03-22 15:34 (UTC+4)

#### Added
- `core/pipeline.py` — `resolve_git_lock()` 함수 (Cowork .git/*.lock 자동 해소)
- `core/cost.py` — `record_session()` 함수 (현재 세션 비용 기록)

---

### v1.0 — `feat: pipeline auto-run + memory engine + SURFACE 4건 리팩터`

**Date**: 2026-03-22 15:21 (UTC+4)

#### Added
- `core/pipeline.py` — 파이프라인 자동 실행 엔진 (dispatch→plan→impl→review→qa→ship→retro 체이닝)
- `core/memory.py` — JSONL 세션 메모리 (저장/로드/로테이션/context.md 생성)
- QA 실패 시 review→fix→qa 자동 재시도 (최대 3회)

#### Changed
- SURFACE 4건 리팩터 반영

---

### v0.2 — `refactor: apply AUTO-FIX 6건 + add test_types.py (16 tests)`

**Date**: 2026-03-22 14:38 (UTC+4)

#### Added
- `tests/test_types.py` — 16 tests (Enum/Dataclass 전수 검증)

#### Changed
- AUTO-FIX 6건 적용 (코드 품질 개선)

---

### v0.1 — `fix: unify skill names to mstack-* prefix, add missing skills to git`

**Date**: 2026-03-22 19:29 (UTC+4)

#### Fixed
- 스킬 이름 통일: `mstack-*` prefix 적용 (plan→mstack-plan 등)
- 누락된 스킬 파일 Git 추가

---

### v0.0 — `init: ccat - Claude Code Agent Teams CLI`

**Date**: 2026-03-22 02:34 (UTC+4)

#### Added
- 프로젝트 초기 구조 생성
- `ccat.py` — Agent Teams 초기화 CLI
- `mstack.py` — 메인 CLI (init/cost/check/upgrade/doctor)
- `core/` — 11 모듈 초기 구현 (types, config, drift, hooks, skills, cost, dashboard, claude_md, doctor, session)
- `skills/` — 8 SDLC 스킬 (plan, review, ship, qa, investigate, retro, careful, dispatch)
- `presets/` — default, hvdc, minimal JSON 프리셋
- `prompts/` — 4 프롬프트 템플릿
- `ci/check.py` — CLAUDE.md 검증 + drift + matrix 생성
- `tests/` — 초기 테스트 스위트
- `pyproject.toml`, `setup.sh`, `.gitignore`

---

## Coverage Trajectory

| Version | Tests | Core Stmts | Miss | Coverage |
|---------|-------|------------|------|----------|
| v0.0 | ~50 | 863 | ~120 | ~86% |
| v0.2 | ~66 | 863 | ~100 | ~88% |
| v1.0 | ~180 | 863 | ~30 | ~96% |
| v1.2 | 225 | 863 | 15 | 98% |
| v1.3 | 235 | 863 | 7 | 99% |
| v1.4 | 241 | 863 | 0 | **100%** |
