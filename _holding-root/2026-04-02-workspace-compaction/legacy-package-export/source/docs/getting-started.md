# mstack 시작하기 (Getting Started)

> 플랫폼: Windows 11 / macOS / Linux
> 대상: mstack을 처음 사용하는 개발자
> 소요 시간: 약 5분

---

## mstack이 뭔가요?

Claude Code를 쓰다 보면 이런 고민이 생깁니다.

- "지금 작업이 혼자 할지, 팀으로 나눠 할지 어떻게 판단하지?"
- "파일 고칠 때마다 테스트 돌리는 걸 자동화하고 싶은데..."
- "CLAUDE.md를 매번 손으로 쓰기 귀찮다"

**mstack은 이 세 가지를 자동화합니다.**

```
mstack init  →  CLAUDE.md + 스킬 7종 + 훅 + settings.json 한 번에 생성
mstack check →  지금 작업에 Claude 단독 / 서브에이전트 / 팀 중 뭐가 맞는지 추천
mstack cost  →  세션 비용 조회 및 대시보드
```

---

## 설치

### 요구사항 확인

```
Python 3.11 이상
Claude Code CLI (claude 명령어)
```

```bash
python --version
# Python 3.12.4  ← 3.11 이상이면 OK
```

### pip으로 설치

```bash
pip install -e /path/to/ccat
```

설치 확인:

```bash
mstack --version
```

실제 출력:
```
mstack 1.1.0
```

---

## 첫 번째 프로젝트에 적용하기

### 1단계: 프로젝트 폴더로 이동

```bash
cd my-project
```

폴더 안에 뭐가 있든 상관없습니다. `mstack init`이 언어를 자동으로 감지합니다.

```
my-project/
├── pyproject.toml   ← 이게 있으면 Python으로 감지
├── src/
│   └── main.py
└── tests/
    └── test_main.py
```

### 2단계: `mstack init` 실행

```bash
mstack init
```

실제 출력:
```
[mstack] Preset: python (python)
[mstack] ✅ Skills: 7 files → .claude/skills/mstack
[mstack] ✅ Hooks: 2 files → .claude/hooks
[mstack] ✅ settings.json → .claude/settings.json
[mstack] ✅ CLAUDE.md → CLAUDE.md (~649 tokens)

[mstack] 🎉 Init complete! Run `claude` to start.
```

완료. 이제 `claude` 명령어로 Claude Code를 시작하면 됩니다.

### 3단계: 생성된 파일 확인

```
my-project/
├── CLAUDE.md                        ← Claude에게 프로젝트 설명하는 파일 (자동 생성)
├── .gitignore                       ← mstack 관련 항목 자동 추가
├── pyproject.toml
├── src/
└── .claude/
    ├── settings.json                ← 훅·환경변수 설정
    ├── skills/
    │   └── mstack/
    │       ├── plan.md              ← /plan 스킬
    │       ├── review.md            ← /review 스킬
    │       ├── ship.md              ← /ship 스킬
    │       ├── qa.md                ← /qa 스킬
    │       ├── investigate.md       ← /investigate 스킬
    │       ├── retro.md             ← /retro 스킬
    │       └── careful.md           ← /careful 스킬
    └── hooks/
        ├── on-task-completed.sh     ← 작업 완료 시 테스트 자동 실행
        └── on-teammate-idle.sh      ← 팀원 유휴 시 다음 작업 안내
```

### 4단계: Claude Code 실행

```bash
claude
```

Claude Code 안에서 이제 스킬을 쓸 수 있습니다:

```
/plan     → 아키텍처 설계
/review   → 코드 리뷰
/ship     → 배포 체크리스트
/qa       → 테스트 실행 + 커버리지
/investigate → 버그 디버깅
/retro    → 주간 회고
/careful  → 위험 명령 실행 전 경고
```

---

## 지금 작업에 뭐가 맞는지 모르겠다면: `mstack check`

파일을 몇 개 수정했는데 Claude 단독으로 할지, 팀으로 나눠 할지 헷갈릴 때 씁니다.

### 파일 2개 수정한 경우

```bash
mstack check --files src/main.py tests/test_main.py
```

실제 출력:
```
👤 Recommendation: SINGLE
  Files: 2
  Reason: Only 2 files — single session sufficient
  Est. cost ratio: 1.0x
```

→ **혼자** 해도 충분합니다.

### 파일 5개, 여러 모듈에 걸쳐 있는 경우

```bash
mstack check --files src/main.py src/api.py src/utils.py tests/test_main.py tests/test_api.py
```

실제 출력:
```
👥 Recommendation: AGENT_TEAMS
  Files: 5
  Reason: Cross-module coordination needed (⚠ ~3.5x tokens)
  Est. cost ratio: 3.5x
  ⚠ Coordination needed — use delegate mode (Shift+Tab)
```

→ **Agent Teams**를 쓰세요. Claude Code에서 `Shift+Tab`으로 위임 모드 전환.

### 판단 기준 한눈에 보기

| 상황 | 권장 모드 | 비용 배율 |
|------|-----------|-----------|
| 파일 1~2개 | 👤 SINGLE | 1.0x |
| 파일 3~4개, 같은 모듈 | 🔀 SUBAGENT | 1.5x |
| 파일 3~4개, 다른 모듈 또는 API 변경 | 👥 AGENT_TEAMS | 3.5x |
| 파일 5개 이상 | 👥 AGENT_TEAMS | 3.5x |

git을 쓰고 있다면 파일 목록을 직접 안 써도 됩니다:

```bash
mstack check
# git diff --name-only HEAD 결과를 자동으로 읽어옵니다
```

---

## 훅(Hook): 자동화 설정

### basic vs extended

`mstack init`의 기본값은 **basic** (훅 2종)입니다.

```bash
# basic (기본): 작업 완료 시 테스트 자동 실행
mstack init

# extended: 보안 게이트 + 포맷 + 비용 기록 추가
mstack init --hooks extended
```

**basic 훅 (2종):**

| 훅 | 동작 |
|----|------|
| TaskCompleted | 작업 끝나면 자동으로 `ruff check .` + `pytest tests/ -x` 실행 |
| TeammateIdle | 팀원이 쉬고 있을 때 다음 할 일 안내 |

**extended 훅 (6종, basic 포함):**

| 훅 | 동작 |
|----|------|
| PreToolUse | `rm -rf /`, `git push --force` 같은 위험 명령 자동 차단 |
| PostToolUse | 파일 수정 후 자동 포맷 실행 |
| Stop | 세션 종료 시 비용 자동 기록 |
| SubagentStop | 서브에이전트 종료 시 결과 기록 |

**extended 적용:**

```bash
mstack init --hooks extended
```

실제 출력:
```
[mstack] Preset: python (python)
[mstack] ✅ Skills: 7 files → .claude/skills/mstack
[mstack] ✅ Hooks: 6 files → .claude/hooks
[mstack] ✅ settings.json → .claude/settings.json
[mstack] ✅ CLAUDE.md → CLAUDE.md (~722 tokens)

[mstack] 🎉 Init complete! Run `claude` to start.
```

생성된 훅 파일:
```
.claude/hooks/
├── on-task-completed.sh
├── on-teammate-idle.sh
├── pre-tool-use.sh        ← 추가됨 (보안 게이트)
├── post-tool-use.sh       ← 추가됨 (자동 포맷)
├── on-stop.sh             ← 추가됨 (비용 기록)
└── on-subagent-stop.sh    ← 추가됨 (서브에이전트 기록)
```

> **Windows 참고**: bash 기반 훅은 Git Bash가 설치되어 있어야 실행됩니다.
> 설치: https://gitforwindows.org

---

## 기존 파일이 있을 때: `--force`

이미 `CLAUDE.md`나 `settings.json`이 있을 때 `mstack init`을 실행하면 기존 파일을 `.bak`으로 백업 후 덮어씁니다.

```bash
mstack init --force
```

```
[mstack] ⚠ Existing settings.json backed up → settings.json.bak
[mstack] ⚠ Existing CLAUDE.md backed up → CLAUDE.md.bak
```

---

## 실제로 어떤 일이 벌어지나: `--dry-run`

파일을 만들기 전에 어떻게 될지 미리 볼 수 있습니다.

```bash
mstack init --dry-run --hooks extended
```

실제 출력:
```
[mstack] Preset: python (python)
[mstack] === DRY RUN ===
  CLAUDE.md (lazy=True)
  skills/ (7 files)
  hooks/ (extended mode)
  settings.json
```

아무 파일도 생성되지 않습니다. 확인 후 `--dry-run`을 빼고 실행하면 됩니다.

---

## 프리셋: 언어별 설정

`mstack init`이 자동으로 언어를 감지하지만, 직접 지정할 수도 있습니다.

| 프리셋 | 감지 조건 | 테스트 명령 |
|--------|-----------|------------|
| `python` | `pyproject.toml`, `*.py` | `pytest tests/ -x` |
| `ts` | `package.json`, `*.ts` | — |
| `go` | `go.mod` | — |
| `rust` | `Cargo.toml` | — |
| `hvdc` | 수동 지정 | `pytest tests/ -x --tb=short` |
| `minimal` | 아무것도 없을 때 | — |

```bash
# TypeScript 프로젝트
mstack init --preset ts

# HVDC 물류 도메인
mstack init --preset hvdc --hooks extended
```

---

## 버전 확인 및 업그레이드

```bash
# 현재 버전 확인
mstack upgrade --check-only
```

실제 출력:
```
[mstack] Current version: 1.1.0
[mstack] Check-only mode. No changes made.
```

```bash
# 업그레이드 실행
mstack upgrade
```

---

## 자주 묻는 질문

**Q. `mstack init` 후에 CLAUDE.md를 수동으로 수정해도 되나요?**
A. 됩니다. `mstack init --force`를 다시 실행하면 덮어쓰므로 주의하세요. 수동 수정 내용은 `.bak` 파일로 백업됩니다.

**Q. 스킬을 추가하거나 수정하고 싶어요.**
A. `.claude/skills/mstack/*.md` 파일을 직접 편집하면 됩니다. Claude Code가 트리거 시 해당 파일을 읽습니다.

**Q. `mstack check`가 항상 AGENT_TEAMS를 권장해요.**
A. 파일을 직접 지정해보세요: `mstack check --files src/main.py`. git 자동 감지가 예상과 다를 수 있습니다.

**Q. Windows에서 훅이 동작을 안 해요.**
A. Git Bash를 설치하세요. 설치 후에도 안 되면 Claude Code의 훅 경로가 bash를 찾지 못하는 경우입니다. `settings.json`의 `command` 경로를 Git Bash 절대 경로로 수정하세요.

**Q. `mstack cost`에 데이터가 없다고 나와요.**
A. extended hooks로 재초기화하면 세션 종료 시 자동 기록됩니다: `mstack init --hooks extended --force`

---

## 전체 명령어 요약

```bash
# 설치
pip install -e /path/to/ccat

# 버전 확인
mstack --version

# 프로젝트 초기화 (기본)
mstack init

# 프리셋·훅 지정
mstack init --preset python --hooks extended

# 결과 미리 보기 (파일 생성 안 함)
mstack init --dry-run

# 기존 파일 덮어쓰기
mstack init --force

# 지금 작업에 맞는 모드 추천
mstack check
mstack check --files src/a.py src/b.py

# 비용 조회
mstack cost
mstack cost --dashboard
mstack cost --threshold 5.0

# 버전 확인
mstack upgrade --check-only
```
