"""core/hooks.py — Hook 스크립트 생성, settings.json Hook 등록"""
from __future__ import annotations
from collections.abc import Callable
from pathlib import Path
import json
import stat
from types import MappingProxyType
from .types import HookEvent, HookConfig, Preset

# ── Timeout 상수 (ms) ────────────────────────────────
TIMEOUT_LONG_MS = 30_000    # 30초 — 테스트 포함 (TaskCompleted)
TIMEOUT_MEDIUM_MS = 5_000   # 5초 — lint, 로깅 등
TIMEOUT_FAST_MS = 200       # 200ms — 핵심 latency 제약 (PreToolUse)


# ── Hook 스크립트 내용 ─────────────────────────────────

def gen_hook_task_completed(preset: Preset) -> str:
    """TaskCompleted hook — 테스트/린트 자동 실행"""
    return f"""#!/usr/bin/env bash
# mstack: TaskCompleted hook — 테스트/린트 자동 실행
# 프리셋: {preset.name}
set -euo pipefail

MSTACK_PY="$(dirname "$0")/../../mstack.py"

echo "[mstack] Running post-task checks..."

# Lint
echo "[mstack] Lint: {preset.lint_cmd}"
{preset.lint_cmd} || {{ echo "[mstack] ❌ Lint failed"; exit 2; }}

# Test
echo "[mstack] Test: {preset.test_cmd}"
{preset.test_cmd} || {{ echo "[mstack] ❌ Tests failed"; exit 2; }}

echo "[mstack] ✅ All checks passed"

# 세션 모드 자동 갱신 (git diff 기반)
echo "[mstack] Refreshing session mode..."
python3 -m mstack check --apply 2>/dev/null || true
python3 "$MSTACK_PY" room-log append --event-type task_completed --sender system --message "task completed checks passed" --hook-event TaskCompleted 2>/dev/null || true

exit 0
"""


def gen_hook_teammate_idle(preset: Preset) -> str:
    """TeammateIdle hook — 다음 작업 할당 가이드"""
    return f"""#!/usr/bin/env bash
# mstack: TeammateIdle hook
set -euo pipefail
MSTACK_PY="$(dirname "$0")/../../mstack.py"
echo "[mstack] Teammate idle. Consider assigning: lint, test, or docs task."
python3 "$MSTACK_PY" room-log append --event-type teammate_idle --sender system --message "teammate idle" --hook-event TeammateIdle 2>/dev/null || true
exit 0
"""


def gen_hook_pre_tool_use() -> str:
    """PreToolUse hook — 파괴적 명령 차단 보안 게이트

    stdin: {"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}
    stdout: {"decision":"approve"} 또는 {"decision":"deny","reason":"..."}
    """
    return r"""#!/usr/bin/env bash
# mstack: PreToolUse security gate
# stdin으로 tool_name + tool_input JSON 수신
# stdout으로 approve/deny JSON 반환

set -euo pipefail

# stdin에서 JSON 읽기
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

# Bash 명령만 검사
if [ "$TOOL_NAME" != "Bash" ]; then
    echo '{"decision":"approve"}'
    exit 0
fi

# ── 차단 패턴 ──
DENY_PATTERNS=(
    "rm -rf /"
    "rm -rf ~"
    "rm -rf \$HOME"
    "rm -rf --no-preserve-root"
    "git push.*--force.*main"
    "git push.*--force.*master"
    "git reset --hard"
    "git clean -fd"
    "DROP TABLE"
    "DROP DATABASE"
    "truncate"
    ":(){ :|:& };:"
    "mkfs"
    "dd if="
    "> /dev/sda"
    "chmod -R 777 /"
    "curl.*\| bash"
    "wget.*\| bash"
)

for pattern in "${DENY_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qiE "$pattern"; then
        REASON="Blocked destructive command matching pattern: $pattern"
        echo "{\"decision\":\"deny\",\"reason\":\"$REASON\"}"

        # 보안 이벤트 로깅
        LOG_DIR="${HOME}/.claude/cost-logs"
        mkdir -p "$LOG_DIR"
        echo "{\"event_type\":\"security_event\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"pattern\":\"$pattern\",\"command\":\"$(echo "$COMMAND" | head -c 200)\"}" >> "$LOG_DIR/cost.jsonl"

        exit 0
    fi
done

echo '{"decision":"approve"}'
exit 0
"""


def gen_hook_post_tool_use(preset: Preset) -> str:
    """PostToolUse hook — 파일 변경 시 자동 포맷팅

    재귀 방지: MSTACK_HOOK_RUNNING=1 체크
    """
    return f"""#!/usr/bin/env bash
# mstack: PostToolUse auto-format hook
set -euo pipefail

# 재귀 방지
if [ "${{MSTACK_HOOK_RUNNING:-0}}" = "1" ]; then
    exit 0
fi
export MSTACK_HOOK_RUNNING=1

# stdin에서 tool 정보 읽기
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null || echo "")

# Write/Edit 도구만 처리
if [ "$TOOL_NAME" != "Write" ] && [ "$TOOL_NAME" != "Edit" ]; then
    exit 0
fi

# 포맷팅 실행 (실패해도 무시)
{preset.lint_cmd} --fix 2>/dev/null || true

unset MSTACK_HOOK_RUNNING
exit 0
"""


def gen_hook_stop() -> str:
    """Stop hook — 세션 종료 시 cost.py log_auto_end 호출로 비용 자동 기록

    v1.2: 직접 JSONL 쓰기 대신 cost.py auto-end 서브커맨드 사용.
    cost.py가 없으면 기존 방식(직접 JSONL)으로 fallback.
    """
    return r"""#!/usr/bin/env bash
# mstack: Stop hook — 세션 비용 자동 로깅 (v1.2: cost.py 연동)
set -euo pipefail

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id','unknown'))" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
MSTACK_PY="$(dirname "$0")/../../mstack.py"

# v1.2: cost.py auto-end 사용 (존재 시)
COST_PY="$(dirname "$0")/../../cost.py"
if [ -f "$COST_PY" ]; then
    python3 "$COST_PY" auto-end --session-id "$SESSION_ID" --ts "$TIMESTAMP" 2>/dev/null || true
else
    # fallback: 직접 JSONL 기록
    LOG_DIR="${HOME}/.claude/cost-logs"
    mkdir -p "$LOG_DIR"
    echo "{\"ev\":\"auto_end\",\"session_id\":\"$SESSION_ID\",\"ts\":\"$TIMESTAMP\"}" >> "$LOG_DIR/sessions.jsonl"
fi

python3 "$MSTACK_PY" room-log append --event-type stop --sender system --message "session stopped" --session-id "$SESSION_ID" --timestamp "$TIMESTAMP" --hook-event Stop 2>/dev/null || true

echo "[mstack] Session logged: $SESSION_ID"
exit 0
"""


def gen_hook_subagent_stop() -> str:
    """SubagentStop hook — 서브에이전트 결과 로깅"""
    return r"""#!/usr/bin/env bash
# mstack: SubagentStop hook — 서브에이전트 완료 로깅
set -euo pipefail

INPUT=$(cat)
MSTACK_PY="$(dirname "$0")/../../mstack.py"
AGENT_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('agent_id') or d.get('subagent_id') or d.get('id') or '')" 2>/dev/null || echo "")
STATUS=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status',''))" 2>/dev/null || echo "")
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

LOG_DIR="${HOME}/.claude/cost-logs"
mkdir -p "$LOG_DIR"

SAFE_DATA=$(echo "$INPUT" | head -c 500 | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" 2>/dev/null || echo '""')
echo "{\"event_type\":\"subagent_end\",\"timestamp\":\"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",\"data\":$SAFE_DATA}" >> "$LOG_DIR/cost.jsonl"

python3 "$MSTACK_PY" room-log append --event-type subagent_end --sender system --message "subagent completed" --timestamp "$TIMESTAMP" --hook-event SubagentStop --agent-id "$AGENT_ID" --status "$STATUS" 2>/dev/null || true

exit 0
"""


# ── Hook 배포 매핑 ─────────────────────────────────────

HookGenerator = Callable[..., str]

HOOK_GENERATORS: MappingProxyType[HookEvent, tuple[str, HookGenerator]] = MappingProxyType({
    HookEvent.TASK_COMPLETED: ("on-task-completed.sh", gen_hook_task_completed),
    HookEvent.TEAMMATE_IDLE: ("on-teammate-idle.sh", gen_hook_teammate_idle),
    HookEvent.PRE_TOOL_USE: ("pre-tool-use.sh", gen_hook_pre_tool_use),
    HookEvent.POST_TOOL_USE: ("post-tool-use.sh", gen_hook_post_tool_use),
    HookEvent.STOP: ("on-stop.sh", gen_hook_stop),
    HookEvent.SUBAGENT_STOP: ("on-subagent-stop.sh", gen_hook_subagent_stop),
})

BASIC_HOOKS = frozenset({HookEvent.TASK_COMPLETED, HookEvent.TEAMMATE_IDLE})
EXTENDED_HOOKS = frozenset(HookEvent)


def deploy_hooks(target_dir: Path, preset: Preset,
                 level: str = "basic") -> list[Path]:
    """Hook 스크립트를 생성하고 실행 권한을 부여한다.

    Args:
        target_dir: hooks/ 디렉토리 경로
        preset: 프로젝트 프리셋
        level: "basic" (2종) | "extended" (6종)

    Returns:
        생성된 Hook 파일 경로 리스트
    """
    events = BASIC_HOOKS if level == "basic" else EXTENDED_HOOKS
    target_dir.mkdir(parents=True, exist_ok=True)
    created = []

    for event in events:
        filename, generator = HOOK_GENERATORS[event]
        path = target_dir / filename

        # 프리셋 필요한 Hook vs 프리셋 불필요한 Hook
        if event in (HookEvent.TASK_COMPLETED, HookEvent.TEAMMATE_IDLE,
                     HookEvent.POST_TOOL_USE):
            content = generator(preset)
        else:
            content = generator()

        path.write_text(content, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IEXEC)
        created.append(path)

    return created


def generate_settings_hooks(hooks_dir: Path, level: str = "basic") -> list[dict]:
    """settings.json의 hooks[] 배열을 생성한다.

    Returns:
        settings.json에 삽입할 hooks 리스트
    """
    events = BASIC_HOOKS if level == "basic" else EXTENDED_HOOKS
    result = []

    # 이벤트별 타임아웃 (모듈 상수 참조)
    TIMEOUTS = {
        HookEvent.TASK_COMPLETED: TIMEOUT_LONG_MS,
        HookEvent.TEAMMATE_IDLE: TIMEOUT_MEDIUM_MS,
        HookEvent.PRE_TOOL_USE: TIMEOUT_FAST_MS,
        HookEvent.POST_TOOL_USE: TIMEOUT_MEDIUM_MS,
        HookEvent.STOP: TIMEOUT_MEDIUM_MS,
        HookEvent.SUBAGENT_STOP: TIMEOUT_MEDIUM_MS,
    }

    for event in events:
        filename, _ = HOOK_GENERATORS[event]
        hook_path = str(hooks_dir / filename)
        matcher: dict[str, str] = {"event": event.value}

        entry = {
            "matcher": matcher,
            "hooks": [{
                "type": "command",
                "command": f"bash {hook_path}",
                "timeout": TIMEOUTS.get(event, 5000),
            }]
        }

        # PreToolUse는 tool_name 필터 추가
        if event == HookEvent.PRE_TOOL_USE:
            matcher["tool_name"] = "Bash"

        # PostToolUse는 Write/Edit만
        if event == HookEvent.POST_TOOL_USE:
            matcher["tool_name"] = "Write|Edit"

        result.append(entry)

    return result


def generate_settings_json(hooks_dir: Path, preset: Preset,
                           level: str = "basic") -> dict:
    """전체 settings.json을 생성한다."""
    hooks = generate_settings_hooks(hooks_dir, level)

    settings = {
        "env": {
            "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
            "MSTACK_PRESET": preset.name,
        },
        "hooks": hooks,
        "permissions": preset.permissions,
    }

    return settings
