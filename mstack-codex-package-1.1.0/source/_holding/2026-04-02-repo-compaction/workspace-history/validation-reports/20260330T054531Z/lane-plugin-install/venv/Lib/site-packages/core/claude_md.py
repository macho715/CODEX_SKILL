"""core/claude_md.py — CLAUDE.md 생성기 (v1.1 Lazy Index + Compaction Rules)"""
from __future__ import annotations
from pathlib import Path
from .types import Preset
from .skills import generate_lazy_index, generate_inline_skills


def generate_claude_md(
    project_name: str,
    dirs: list[str],
    preset: Preset,
    skills_path: str = ".claude/skills/mstack",
    hooks_level: str = "basic",
    lazy_skills: bool = True,
) -> str:
    """CLAUDE.md 전체 내용을 생성한다.

    v1.1:
    - lazy_skills=True: 스킬 요약 Lazy Index만 포함 (토큰 절감)
    - lazy_skills=False: 각 스킬별 상세 설명 embed (inline, 토큰 많음)
    - Compaction Rules 섹션 추가
    - Hook 설명 확장 (6 이벤트)

    Args:
        project_name: 프로젝트 이름
        dirs: 프로젝트 디렉토리 목록
        preset: 프리셋 설정
        skills_path: 스킬 파일 상대 경로
        hooks_level: "basic" | "extended"
        lazy_skills: True면 인덱스만, False면 전문 포함
    """
    sections = []

    # ── Header ──
    sections.append(f"# {project_name}")
    sections.append("")

    # ── Project Structure ──
    sections.append("## Project Structure")
    sections.append(f"Language: {preset.lang.value}")
    sections.append(f"Directories: {', '.join(dirs)}")
    sections.append("")

    # ── Commands ──
    sections.append("## Commands")
    sections.append(f"- Test: `{preset.test_cmd}`")
    sections.append(f"- Lint: `{preset.lint_cmd}`")
    sections.append(f"- Type check: `{preset.type_cmd}`")
    sections.append("")

    # ── Rules ──
    sections.append("## Rules")
    if preset.rules:
        for rule in preset.rules:
            sections.append(f"- {rule}")
    # v1.2: 글로벌 상수 보호 + debug 테스트 격리 규칙
    sections.append("- Module-level dicts/lists used as constants MUST use MappingProxyType or tuple (no mutable globals)")
    sections.append("- Test files that mutate global state must use pytest fixtures with proper teardown, not manual backup/restore")
    sections.append("- Debug tests in `tests/debug/` are excluded from collection (`--ignore=tests/debug`)")
    sections.append("")

    # ── Skills (v1.1: Lazy Index 또는 Inline) ──
    if lazy_skills:
        sections.append(generate_lazy_index())
    else:
        sections.append(generate_inline_skills())
    sections.append("")

    # ── Agent Teams Routing Guide ──
    sections.append("## Agent Teams Routing")
    sections.append(_gen_routing_guide())
    sections.append("")

    # ── Hooks ──
    sections.append("## Hooks")
    sections.append(_gen_hooks_description(hooks_level))
    sections.append("")

    # ── HVDC Domain (프리셋별) ──
    if preset.domain_terms:
        sections.append("## Domain Terms")
        for term, desc in preset.domain_terms.items():
            sections.append(f"- **{term}**: {desc}")
        sections.append("")

    if preset.fanr_rules:
        sections.append("## FANR/MOIAT Compliance")
        for rule in preset.fanr_rules:
            sections.append(f"- {rule}")
        sections.append("")

    # ── Compaction Rules (v1.1 NEW) ──
    sections.append(_gen_compaction_rules(preset))

    return "\n".join(sections)


def _gen_routing_guide() -> str:
    """Agent Teams 라우팅 가이드 (CLAUDE.md 포함)"""
    return """### When to use Agent Teams vs Subagent

**Use Subagent when:**
- Task is self-contained (no coordination with other tasks)
- Delegating verbose ops: running tests, fetching docs, processing logs
- Each worker's task is fully describable without referencing other workers

**Use Agent Teams when:**
- Modifying 5+ files across different modules
- Frontend + Backend coordination needed (API contract sync)
- Multiple reviewers needed (security + performance + quality)
- Workers need to share findings or challenge each other

**Cost awareness:**
- Subagent: ~1x tokens (result summary only returns to parent)
- Agent Teams: ~3-4x tokens (each teammate has own context)
- Agent Teams in plan mode: ~7x tokens"""


def _gen_hooks_description(level: str) -> str:
    """Hook 설명 (basic/extended)"""
    basic = """- **TaskCompleted**: Auto-runs lint + test after each task
- **TeammateIdle**: Suggests next task assignment"""

    extended_extra = """
- **PreToolUse** (security gate): Blocks destructive commands (rm -rf, force push, DROP TABLE)
- **PostToolUse** (auto-format): Runs formatter after Write/Edit operations
- **Stop** (cost logging): Logs session cost to JSONL on session end
- **SubagentStop** (logging): Logs subagent results
- **Room Logs**: Extended hooks can append room-based group activity logs under `.claude/group-logs/`"""

    if level == "extended":
        return basic + extended_extra
    return basic


def _gen_compaction_rules(preset: Preset) -> str:
    """v1.1 NEW: Compaction Rules — Claude Code 자동 요약 시 보존 항목"""
    return f"""## Compaction Rules

> When Claude Code compacts this context, ALWAYS preserve:

1. **Project commands**: `{preset.test_cmd}`, `{preset.lint_cmd}`, `{preset.type_cmd}`
2. **Modified files list**: All files changed in this session
3. **Current task goal**: The objective being worked on
4. **KPI targets**: Agent Teams cost ≤31%, Hook coverage ≥50%
5. **Skill triggers**: /plan, /review, /ship, /qa, /investigate, /retro, /careful
6. **Safety rules**: PreToolUse patterns, NDA/PII masking rules"""


def measure_token_count(text: str) -> int:
    """대략적 토큰 수 계산 (chars / 4 근사치)"""
    return len(text) // 4
