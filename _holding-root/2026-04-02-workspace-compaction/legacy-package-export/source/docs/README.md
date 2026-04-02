# mstack (ccat) — Claude Code Agent Teams CLI

> Modular SDLC pipeline engine for Claude Code multi-agent workflows.

## Overview

mstack는 Claude Code 환경에서 Agent Teams 기반 소프트웨어 개발 라이프사이클(SDLC)을 자동화하는 CLI 도구입니다. 프로젝트 초기화, 비용 추적, 환경 진단, 파이프라인 자동 실행, 세션 메모리까지 하나의 패키지로 제공합니다.

## Features

- **Smart Router** — 파일 수·모듈 의존성 분석으로 SINGLE / SUBAGENT / AGENT_TEAMS 모드 자동 추천
- **Pipeline Auto-Run** — dispatch 승인 후 plan→구현→review→qa→ship→retro 자동 체이닝 (QA 실패 시 최대 3회 재시도)
- **Session Memory** — JSONL 기반 세션 결과 저장, 다음 세션에서 자동 컨텍스트 로드 (최근 100 세션 로테이션)
- **Cost Tracking** — 모델별·날짜별·세션별 비용 집계 + Chart.js 인터랙티브 대시보드
- **8 SDLC Skills** — plan, review, ship, qa, investigate, retro, careful, dispatch
- **Hook Automation** — TaskCompleted, TeammateIdle, PreToolUse, PostToolUse 이벤트 기반 lint/test/typecheck 자동 실행
- **Multi-Language** — Python, TypeScript, Go, Rust 프리셋 지원

## Quick Start

```bash
# 1. 프로젝트 초기화
./setup.sh          # 또는 python ccat.py

# 2. CLI 사용
mstack init         # .claude/ 디렉토리 + hooks + settings 생성
mstack doctor       # 환경 진단 (Python, pip, pytest, git, formatter)
mstack cost         # 비용 리포트 (ASCII table + HTML dashboard)
mstack check        # CLAUDE.md 유효성 + 구조 drift 검증
mstack upgrade      # 프로젝트 업그레이드 스카우트
```

## Requirements

- Python 3.11+
- pip (pytest, flake8, mypy 권장)
- Git

## Installation

```bash
pip install -e .
```

## Testing

```bash
# 전체 테스트 (241 tests, core/ 100% coverage)
python -m pytest tests/ -v --tb=short

# 커버리지 리포트
python -m pytest tests/ --cov=core --cov-report=term-missing

# 린트 + 타입 체크
flake8 core/ --max-line-length 120 --select=E9,F63,F7,F82
python -m mypy core/ --ignore-missing-imports
```

## SDLC Pipeline Skills

```
/plan → /review → /ship → /qa → /investigate → /retro
                                                 ↑
/careful ─── 전 단계 안전 가드레일 ──────────────┘
/dispatch ── 작업 오케스트레이터 (자동 추천 + 실행)
```

| Skill | Role |
|-------|------|
| `/plan` | 2-Phase 구현 계획 (CEO Review + Eng Review) |
| `/review` | AUTO-FIX / SURFACE 분류 코드 리뷰 |
| `/ship` | 테스트 부트스트랩 + 커버리지 감사 + 커밋 |
| `/qa` | Diff-aware / Full / Quick 3-mode 테스트 |
| `/investigate` | 가설 3개 → 검증 → 읽기 전용 조사 |
| `/retro` | Keep/Improve/Learn 회고 + 비용 분석 |
| `/careful` | force push 금지, 시크릿 노출 방지 |
| `/dispatch` | SINGLE/SUBAGENT/AGENT_TEAMS 자동 라우팅 |

## Coding Standards

- Python 3.11+, Type hints 필수
- bare except 금지
- Module-level mutable globals 금지 (MappingProxyType / tuple 사용)
- core/ 커버리지 ≥99%, 신규 모듈 100%
- 기존 모듈 수정 시 커버리지 하락 금지

## Project Version

- Current: **v1.1.0**
- Tests: 241 passed, 1 skipped
- Coverage: core/ 100% (863 stmts, 0 miss, 13/13 modules)

## License

Internal — Samsung C&T / HVDC Project
