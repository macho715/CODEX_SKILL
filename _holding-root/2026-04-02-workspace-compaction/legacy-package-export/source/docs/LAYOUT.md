# Project Layout — mstack (ccat)

## Directory Tree

```
mstack/
├── ccat.py                    # Claude Code Agent Teams 초기화 CLI (521 lines)
├── mstack.py                  # mstack 메인 CLI (366 lines)
├── cost.py                    # 비용 추적 래퍼 (root-level)
├── setup.sh                   # 설치 스크립트 (→ ccat.py 래퍼)
├── pyproject.toml             # 프로젝트 메타데이터 + pytest/setuptools 설정
├── CLAUDE.md                  # AI 에이전트 컨텍스트 문서 (자동 생성)
├── .gitignore                 # Git 제외 패턴
│
├── core/                      # 핵심 라이브러리 (13 modules, 863 stmts, 100% coverage)
│   ├── __init__.py            #   패키지 초기화 + public API re-export
│   ├── types.py               #   공통 Enum/Dataclass 정의
│   ├── config.py              #   프리셋 로더 + 언어 자동 감지
│   ├── drift.py               #   파일 drift 탐지 + Smart Router
│   ├── pipeline.py            #   SDLC 파이프라인 자동 실행 엔진
│   ├── memory.py              #   JSONL 세션 메모리 (저장/로드/로테이션)
│   ├── session.py             #   세션 상태 관리 (JSON + TTL)
│   ├── hooks.py               #   이벤트 훅 bash 스크립트 생성
│   ├── skills.py              #   스킬 배포 + Lazy Index
│   ├── cost.py                #   비용 JSONL 파싱 + 집계
│   ├── dashboard.py           #   Chart.js HTML 대시보드 생성
│   ├── claude_md.py           #   CLAUDE.md 자동 생성기
│   └── doctor.py              #   환경 진단 (mstack doctor)
│
├── tests/                     # 테스트 스위트 (241 tests, 1 skipped)
│   ├── __init__.py
│   ├── conftest.py            #   공유 fixtures
│   ├── test_types.py          #   types.py 16 tests
│   ├── test_config.py         #   config.py tests
│   ├── test_drift.py          #   drift.py tests
│   ├── test_pipeline.py       #   pipeline.py tests (resolve_git_lock 포함)
│   ├── test_memory.py         #   memory.py tests (blank line, rotation)
│   ├── test_session.py        #   session.py tests (corrupt JSON, TTL)
│   ├── test_hooks.py          #   hooks.py tests
│   ├── test_skills.py         #   skills.py tests (deploy, missing source)
│   ├── test_cost_core.py      #   core/cost.py tests (parse, aggregate)
│   ├── test_cost.py           #   root cost.py tests
│   ├── test_cost_3tier.py     #   3-tier cost validation
│   ├── test_dashboard.py      #   dashboard.py tests (browser, subprocess)
│   ├── test_claude_md.py      #   claude_md.py tests
│   ├── test_doctor.py         #   doctor.py tests (_run_cmd, CLI, format)
│   ├── test_context_size.py   #   컨텍스트 사이즈 검증
│   └── debug/                 #   디버그 전용 테스트 (pytest에서 제외)
│
├── skills/                    # SDLC 스킬 소스 (8 directories)
│   ├── plan/SKILL.md          #   구현 계획 수립 (2-Phase)
│   ├── review/SKILL.md        #   코드 리뷰 (AUTO-FIX / SURFACE)
│   ├── ship/SKILL.md          #   배포 준비 (테스트 + 커밋)
│   ├── qa/SKILL.md            #   QA 검증 (Diff/Full/Quick)
│   ├── investigate/SKILL.md   #   버그 조사 (가설 3개)
│   ├── retro/SKILL.md         #   회고 (Keep/Improve/Learn)
│   ├── careful/SKILL.md       #   안전 가드레일
│   └── dispatch/SKILL.md      #   작업 오케스트레이터
│
├── presets/                   # 언어별 설정 프리셋 (JSON)
│   ├── default.json           #   기본 프리셋
│   ├── hvdc.json              #   HVDC 프로젝트 전용
│   └── minimal.json           #   최소 설정
│
├── prompts/                   # 프롬프트 템플릿
│   ├── 01-review.md           #   코드 리뷰 프롬프트
│   ├── 02-feature.md          #   기능 개발 프롬프트
│   ├── 03-debug.md            #   디버그 프롬프트
│   └── 04-refactor.md         #   리팩터링 프롬프트
│
├── ci/                        # CI/CD 유틸리티
│   ├── check.py               #   CLAUDE.md 검증 + drift 탐지 + matrix 생성
│   └── __pycache__/
│
├── docs/                      # 프로젝트 문서
│   ├── getting-started.md     #   시작 가이드
│   ├── user-guide.md          #   사용자 가이드
│   ├── README.md              #   프로젝트 README
│   ├── ARCHITECTURE.md        #   시스템 아키텍처
│   ├── LAYOUT.md              #   이 문서
│   └── CHANGELOG.md           #   변경 이력
│
├── skills-workspace/          # 스킬 개발 워크스페이스 (103 files)
│   ├── iteration-1/           #   1차 이터레이션 eval 결과
│   ├── iteration-2/           #   2차 이터레이션 eval 결과
│   ├── iteration-3/           #   3차 시너지 테스트 결과
│   ├── iteration-4/           #   4차 이터레이션
│   ├── packages-v1.1-unified/ #   v1.1 통합 패키지
│   ├── packages-v1.2/         #   v1.2 패키지 (8 .skill files)
│   └── packages-v1.4/         #   v1.4 최종 패키지 (8 .skill files)
│
├── .claude/                   # Claude Code 설정
│   ├── commands/              #   커맨드 정의
│   └── skills/mstack/         #   설치된 스킬 (skills/ 미러)
│       ├── plan/SKILL.md
│       ├── review/SKILL.md
│       ├── ship/SKILL.md
│       ├── qa/SKILL.md
│       ├── investigate/SKILL.md
│       ├── retro/SKILL.md
│       ├── careful/SKILL.md
│       └── dispatch/SKILL.md
│
├── .github/workflows/         # GitHub Actions
│
└── mstack.egg-info/           # setuptools 빌드 메타데이터
```

## File Count Summary

| Directory | Files | Description |
|-----------|-------|-------------|
| `core/` | 13 | 핵심 라이브러리 (100% coverage) |
| `tests/` | 18 | 테스트 스위트 (241 tests) |
| `skills/` | 8 | SDLC 스킬 소스 |
| `presets/` | 3 | 언어별 프리셋 |
| `prompts/` | 4 | 프롬프트 템플릿 |
| `ci/` | 1 | CI 유틸리티 |
| `docs/` | 6 | 프로젝트 문서 |
| `skills-workspace/` | ~103 | 스킬 개발 + 패키지 |
| Root | 8 | 진입점 + 설정 파일 |

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | 패키지 메타, pytest 설정, setuptools 빌드 |
| `CLAUDE.md` | AI 에이전트 프로젝트 컨텍스트 (자동 생성) |
| `.gitignore` | Git 추적 제외 패턴 |
| `setup.sh` | ccat.py 래퍼 스크립트 |

## Naming Conventions

- **Core modules**: snake_case (`core/claude_md.py`)
- **Test files**: `test_` prefix (`tests/test_drift.py`)
- **Skill directories**: kebab-case in installed form (`mstack-plan`), flat in source (`plan/`)
- **Presets**: descriptive name (`hvdc.json`, `minimal.json`)
- **Prompts**: numbered prefix (`01-review.md`)
