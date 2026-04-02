# ccat — Claude Code Agent Teams CLI

## Codex wheel install

For installing the packaged MStack Codex skills on another computer, see
[INSTALL_CODEX.md](./INSTALL_CODEX.md).

Claude Code Agent Teams 프로젝트를 한 줄로 초기화하는 CLI 킷.

`CLAUDE.md`, hooks, 프롬프트 템플릿, 비용 추적까지 자동 생성한다.

## 빠른 시작

```bash
# 프로젝트 폴더에서 실행 (언어 자동 감지)
python3 ccat.py init /path/to/project

# 언어 직접 지정
python3 ccat.py init . --lang typescript
```

생성되는 파일:

```
~/.claude/settings.json          # Agent Teams 설정 (기존 설정과 병합)
~/.claude/hooks/
  on-task-completed.sh           # 태스크 완료 시 test/lint/typecheck 자동 검증
  on-teammate-idle.sh            # 유휴 팀원에게 pending 태스크 할당
<project>/
  CLAUDE.md                      # 프로젝트 컨텍스트 (구조, 규칙, 검증 명령어)
  .claude-prompts/               # Agent Teams 프롬프트 템플릿
  cost.py                        # 세션별 비용 기록/조회
```

## 명령어

### `init` — 프로젝트 초기화

```bash
python3 ccat.py init [프로젝트 경로] [--lang python|typescript|go|rust]
```

- 프로젝트 파일(`pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`)로 언어 자동 감지
- 기존 `settings.json`이 있으면 덮어쓰지 않고 병합
- 기존 `CLAUDE.md`는 `.md.bak`으로 백업

### `cost` — 비용 시뮬레이션

```bash
python3 ccat.py cost --members 3 --tokens 350000
```

All Opus / Opus+Sonnet / 3-Tier 구성별 세션당·월간 비용을 비교한다.

### `presets` — 언어 프리셋 목록

```bash
python3 ccat.py presets
```

## 프롬프트 템플릿

`.claude-prompts/`에 4가지 시나리오별 팀 구성 템플릿이 포함된다:

| 파일 | 용도 | 팀 구성 |
|------|------|---------|
| `01-review.md` | 코드 리뷰 | 보안 + 성능 + 품질 리뷰어 (3명, Sonnet) |
| `02-feature.md` | 기능 구현 | 역할A + 역할B + 테스트 엔지니어 (3명, Sonnet) |
| `03-debug.md` | 디버깅 | 가설별 조사관 3명 (Sonnet) |
| `04-refactor.md` | 리팩토링 | 설계자(Opus) + 구현자 + 테스트(Sonnet), worktree 격리 |

`{기능}`, `{역할A}` 등 플레이스홀더를 채워서 사용한다.

## 비용 추적

```bash
# 세션 시작 기록
python3 cost.py start --team my-feature -n 3 --mix

# 세션 종료 기록
python3 cost.py end --team my-feature --ti 200000 --to 50000

# 월별 리포트
python3 cost.py report --month 2026-03
```

## CI / GitHub Actions

`.github/workflows/`에 4개 워크플로우가 포함된다:

| 워크플로우 | 트리거 | 역할 |
|-----------|--------|------|
| `validate.yml` | PR, push(main) | CLAUDE.md 필수 섹션 + Hook 문법 검증 |
| `drift.yml` | PR (소스 변경) | 디렉토리 구조 vs CLAUDE.md 불일치 감지 |
| `sync.yml` | push(main), 수동 | 구조 변경 시 `ccat init` 재실행 → PR 자동 생성 |
| `cost-report.yml` | 매주 월요일, 수동 | 주간 비용 리포트 → GitHub Issue 생성 |

## 지원 언어

| 프리셋 | 테스트 | 린트 | 타입체크 |
|--------|--------|------|----------|
| python | pytest | flake8 | mypy |
| typescript | npm test | eslint | tsc --noEmit |
| go | go test | golangci-lint | — |
| rust | cargo test | cargo clippy | — |

## 구조

```
ccat.py              # 메인 CLI (init, cost, presets)
cost.py              # 세션별 비용 기록/조회
setup.sh             # ccat.py 래퍼
prompts/             # Agent Teams 프롬프트 템플릿 (4종)
ci/
  check.py           # CI 유틸 (validate, drift, gen-matrix)
  cost-push.sh       # 로컬 비용 로그 → Git push
.github/workflows/   # GitHub Actions (4종)
```

## 요구사항

- Python 3.11+
- Claude Code CLI (`claude`)
- Git (CI 워크플로우 사용 시)
