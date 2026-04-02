#!/usr/bin/env python3
"""mstack.py — MACHO-STACK CLI entry point

Usage:
    mstack init [--preset NAME] [--lang LANG] [--hooks basic|extended] [--force] [--dry-run]
    mstack cost [--dashboard] [--threshold USD] [--output PATH] [--no-open]
    mstack check [--files FILE...]
    mstack room-log bind --room-name NAME [--room-slug SLUG] [--json]
    mstack room-log append --event-type TYPE --sender SENDER --message TEXT [--room-name NAME] [--room-slug SLUG]
    mstack room-log tail [--room-name NAME] [--room-slug SLUG] [--limit N] [--json]
    mstack pipeline <request> [--mode single|subagent|agent_teams] [--allow-single-agent-fallback] [--external-executor codex] [--generic-implement none|notes] [--json]
    mstack upgrade [--check-only]
"""
from __future__ import annotations
import argparse
import os
import sys
import json
from pathlib import Path

# ── 패키지 루트 ──
MSTACK_ROOT = Path(__file__).parent

from core.assets import install_codex_skills
from core.config import resolve_preset, scan_dirs, detect_lang
from core.skills import deploy_skills, generate_lazy_index, measure_skill_tokens, packaged_skills_dir
from core.hooks import deploy_hooks, generate_settings_json
from core.claude_md import generate_claude_md, measure_token_count
from core.cost import parse_jsonl, aggregate, format_ascii_table
from core.dashboard import generate_dashboard_html, save_and_open, check_threshold
from core.group_logs import append_group_message, ensure_room, slugify_room_name, tail_room_messages, utc_now
from core.drift import (
    smart_route, detect_cross_module, detect_api_contract,
    check_drift, compute_hash,
)
from core.session import (
    write_session, patch_claude_md, patch_settings_env, resolve_room_binding,
    set_room_binding,
)
from core.doctor import run_all_checks, format_results, format_results_json
from core.pipeline_adapter import run_pipeline_request
from core.pipeline_generic_backends import build_generic_implement_backend
from core.parallel_executor import build_codex_exec_parallel_executor
from core.pipeline_recipes import ImplementRecipeContext, detect_parallel_executor_capabilities
from core.pipeline_runner import build_stage_runner
from core.types import (
    GroupMessageEntry,
    PipelineRequestClassifierInput,
    RouterDecision,
    RouterResult,
    StageStatus,
)

__version__ = "1.1.0"

MODE_TO_COST_RATIO = {
    "single": 1.0,
    "subagent": 1.5,
    "agent_teams": 3.5,
}


def _cmd_room_log_help(parser: argparse.ArgumentParser) -> int:
    """Print help for the room-log command when no subcommand is provided."""
    parser.print_help()
    return 0


def _cmd_install_codex_help(parser: argparse.ArgumentParser) -> int:
    """Print help for the install-codex command when needed."""
    parser.print_help()
    return 0


# ═══════════════════════════════════════════════════════
#  INIT
# ═══════════════════════════════════════════════════════

def cmd_init(args: argparse.Namespace) -> int:
    """프로젝트 초기화: CLAUDE.md + skills/ + hooks/ + settings.json"""
    project_dir = Path.cwd()
    lazy = not args.no_lazy  # 기본: lazy=True (v1.1)

    # 1. 프리셋 결정
    preset = resolve_preset(
        project_dir, args.preset, args.lang, None
    )
    print(f"[mstack] Preset: {preset.name} ({preset.lang.value})")

    # 2. 디렉토리 스캔
    dirs = scan_dirs(project_dir)

    # 3. Dry-run 모드
    if args.dry_run:
        print("[mstack] === DRY RUN ===")
        print(f"  CLAUDE.md (lazy={lazy})")
        print(f"  skills/ ({len(['plan','review','ship','qa','investigate','retro','careful'])} files)")
        print(f"  hooks/ ({args.hooks} mode)")
        print(f"  settings.json")
        return 0

    # 4. Skills 배포
    skills_target = project_dir / ".claude" / "skills" / "mstack"
    created_skills = deploy_skills(packaged_skills_dir(), skills_target)
    print(f"[mstack] ✅ Skills: {len(created_skills)} files → {skills_target}")

    # 5. Hooks 배포
    hooks_target = project_dir / ".claude" / "hooks"
    created_hooks = deploy_hooks(hooks_target, preset, args.hooks)
    print(f"[mstack] ✅ Hooks: {len(created_hooks)} files → {hooks_target}")

    # 6. settings.json
    settings = generate_settings_json(hooks_target, preset, args.hooks)
    settings_path = project_dir / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)

    if settings_path.exists() and not args.force:
        bak = settings_path.with_suffix(".json.bak")
        settings_path.rename(bak)
        print(f"[mstack] ⚠ Existing settings.json backed up → {bak.name}")

    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False))
    print(f"[mstack] ✅ settings.json → {settings_path}")

    # 7. CLAUDE.md
    claude_md = generate_claude_md(
        project_name=project_dir.name,
        dirs=dirs,
        preset=preset,
        hooks_level=args.hooks,
        lazy_skills=lazy,
    )
    claude_path = project_dir / "CLAUDE.md"

    if claude_path.exists() and not args.force:
        bak = claude_path.with_suffix(".md.bak")
        claude_path.rename(bak)
        print(f"[mstack] ⚠ Existing CLAUDE.md backed up → {bak.name}")

    claude_path.write_text(claude_md, encoding="utf-8")
    token_count = measure_token_count(claude_md)
    print(f"[mstack] ✅ CLAUDE.md → {claude_path} (~{token_count} tokens)")

    # 8. .gitignore 추가
    gitignore = project_dir / ".gitignore"
    ignore_lines = ["# mstack", ".claude/cost-logs/", "*.bak"]
    if gitignore.exists():
        existing = gitignore.read_text()
        new_lines = [l for l in ignore_lines if l not in existing.splitlines()]
        if new_lines:
            with gitignore.open("a") as f:
                f.write("\n" + "\n".join(new_lines) + "\n")
    else:
        gitignore.write_text("\n".join(ignore_lines) + "\n")

    # 9. 초기 세션 모드 자동 설정 (git diff 기반)
    if not args.dry_run:
        import subprocess as _sp
        try:
            _res = _sp.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, cwd=project_dir, check=True
            )
            _init_files = [f for f in _res.stdout.strip().split("\n") if f]
            if _init_files:
                _route = smart_route(
                    changed_files=_init_files,
                    has_api_contract=detect_api_contract(_init_files),
                    has_cross_module_deps=detect_cross_module(_init_files),
                    cost_sensitive=True,
                )
                write_session(project_dir, _route, _init_files)
                patch_claude_md(project_dir, _route)
                patch_settings_env(project_dir, _route)
                icon = {"single": "👤", "subagent": "🔀", "agent_teams": "👥"}
                print(f"[mstack] {icon[_route.decision.value]} Session mode: {_route.decision.value.upper()}")
        except _sp.CalledProcessError as e:
            print(f"⚠️  git diff failed: {e.stderr}", file=sys.stderr)
            # Fallback: no git diff available, skip session mode detection

    print(f"\n[mstack] 🎉 Init complete! Run `claude` to start.")
    return 0


def cmd_install_codex(args: argparse.Namespace) -> int:
    """Install packaged Codex skills into the target directory."""
    target_dir = Path(args.target).expanduser()
    try:
        result = install_codex_skills(target_dir, force=args.force, dry_run=args.dry_run)
    except FileExistsError as exc:
        print(f"[mstack] ❌ {exc}", file=sys.stderr)
        return 1

    print(f"[mstack] Codex target: {result.target_dir}")
    print(f"[mstack] Installed: {len(result.installed)}")
    print(f"[mstack] Skipped: {len(result.skipped)}")
    print(f"[mstack] Overwritten: {len(result.overwritten)}")
    if result.installed:
        print(f"[mstack] Installed names: {', '.join(result.installed)}")
    if result.skipped:
        print(f"[mstack] Skipped names: {', '.join(result.skipped)}")
    if result.overwritten:
        print(f"[mstack] Overwritten names: {', '.join(result.overwritten)}")
    return 0


# ═══════════════════════════════════════════════════════
#  COST
# ═══════════════════════════════════════════════════════

def cmd_cost(args: argparse.Namespace) -> int:
    """비용 조회 / 대시보드 / 알림"""
    log_path = Path.home() / ".claude" / "cost-logs" / "cost.jsonl"
    entries = parse_jsonl(log_path)

    if not entries:
        print("[mstack] No cost data yet. Run a Claude Code session first.")
        return 0

    data = aggregate(entries)

    # Threshold 체크
    if args.threshold:
        check_threshold(data, args.threshold)

    # 대시보드 모드
    if args.dashboard:
        html = generate_dashboard_html(data)
        out = Path(args.output) if args.output else Path.cwd() / "mstack-dashboard.html"
        save_and_open(html, out, args.no_open)
        print(f"[mstack] ✅ Dashboard → {out}")
        return 0

    # ASCII 테이블 (기본)
    print(format_ascii_table(data))
    return 0


# ═══════════════════════════════════════════════════════
#  CHECK
# ═══════════════════════════════════════════════════════

def cmd_check(args: argparse.Namespace) -> int:
    """드리프트 탐지 + Agent Teams 라우터"""
    project_dir = Path.cwd()

    # CLAUDE.md 존재 확인
    if not (project_dir / "CLAUDE.md").exists():
        print("[mstack] ❌ CLAUDE.md not found. Run `mstack init` first.")
        return 1

    # Smart Router
    if args.files:
        changed_files = args.files
    else:
        # git diff에서 변경 파일 추출
        import subprocess
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                capture_output=True, text=True, cwd=project_dir, check=True
            )
            changed_files = [f for f in result.stdout.strip().split("\n") if f]
        except subprocess.CalledProcessError as e:
            print(f"⚠️  git diff failed: {e.stderr}", file=sys.stderr)
            changed_files = []

    if not changed_files:
        print("[mstack] ✅ No changed files detected. All clear.")
        return 0

    cross_module = detect_cross_module(changed_files)
    api_contract = detect_api_contract(changed_files)

    route = smart_route(
        changed_files=changed_files,
        has_api_contract=api_contract,
        has_cross_module_deps=cross_module,
        cost_sensitive=True,
    )

    # 출력
    icon = {"single": "👤", "subagent": "🔀", "agent_teams": "👥"}
    print(f"\n{icon[route.decision.value]} Recommendation: {route.decision.value.upper()}")
    print(f"  Files: {route.file_count}")
    print(f"  Reason: {route.reason}")
    print(f"  Est. cost ratio: {route.estimated_cost_ratio}x")
    if route.coordination_needed:
        print(f"  ⚠ Coordination needed — use delegate mode (Shift+Tab)")

    # --apply: 세션 상태 파일 + CLAUDE.md 배너 + settings.json env 갱신
    if getattr(args, "apply", False):
        write_session(project_dir, route, changed_files)
        patch_claude_md(project_dir, route)
        patch_settings_env(project_dir, route)
        print(f"\n[mstack] ✅ Session mode applied: {route.decision.value.upper()}")
        print(f"[mstack]    → .claude/session.json updated (30min TTL)")

    return 0


# ═══════════════════════════════════════════════════════
#  ROOM LOG
# ═══════════════════════════════════════════════════════

def _room_log_metadata_from_args(args: argparse.Namespace) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for key in ("hook_event", "tool_name", "stage", "status", "agent_id"):
        value = getattr(args, key, None)
        if value:
            metadata[key] = value
    return metadata


def _resolve_room_args(args: argparse.Namespace, project_dir: Path) -> tuple[str | None, str | None]:
    room_name, room_slug = resolve_room_binding(project_dir, os.environ)
    if getattr(args, "room_name", None):
        room_name = args.room_name
    if getattr(args, "room_slug", None):
        room_slug = args.room_slug
    return room_name, room_slug


def cmd_room_log_append(args: argparse.Namespace) -> int:
    project_dir = Path.cwd()
    room_name, room_slug = _resolve_room_args(args, project_dir)
    if not room_name:
        print("[mstack] ❌ No room configured. Use --room-name on the first append.", file=sys.stderr)
        return 1

    entry = GroupMessageEntry(
        room_name=room_name,
        room_slug=room_slug or "",
        event_type=args.event_type,
        sender=args.sender,
        message=args.message,
        timestamp=args.timestamp or utc_now(),
        session_id=args.session_id or "",
        metadata=_room_log_metadata_from_args(args),
    )
    path = append_group_message(project_dir, entry)
    set_room_binding(project_dir, room_name, path.parent.name)
    print(path)
    return 0


def cmd_room_log_bind(args: argparse.Namespace) -> int:
    project_dir = Path.cwd()
    meta = ensure_room(project_dir, args.room_name, args.room_slug)
    set_room_binding(project_dir, meta.display_name, meta.room_slug)
    payload = {
        "room_name": meta.display_name,
        "room_slug": meta.room_slug,
        "room_dir": str((project_dir / ".claude" / "group-logs" / meta.room_slug)),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(payload["room_dir"])
    return 0


def cmd_room_log_tail(args: argparse.Namespace) -> int:
    project_dir = Path.cwd()
    room_name, room_slug = _resolve_room_args(args, project_dir)
    if not room_slug and room_name:
        room_slug = slugify_room_name(room_name)
    if not room_slug:
        print("[mstack] ❌ No room configured. Use --room-slug or append a room log first.", file=sys.stderr)
        return 1

    entries = tail_room_messages(
        project_dir,
        room_slug,
        limit=args.limit,
        max_chars=args.max_chars,
    )
    if args.json:
        print(json.dumps([entry.__dict__ for entry in entries], ensure_ascii=False, indent=2))
        return 0

    if not entries:
        print("[mstack] No room log entries found.")
        return 0

    for entry in entries:
        print(f"[{entry.timestamp}] {entry.sender}/{entry.event_type}: {entry.message}")
    return 0


# ═══════════════════════════════════════════════════════
#  PIPELINE
# ═══════════════════════════════════════════════════════

def _build_pipeline_router_result(mode: str | None) -> RouterResult | None:
    """Build an optional RouterResult from CLI mode override."""
    if mode is None:
        return None

    decision = RouterDecision(mode)
    return RouterResult(
        decision=decision,
        reason="cli override",
        file_count=0,
        coordination_needed=decision == RouterDecision.AGENT_TEAMS,
        estimated_cost_ratio=MODE_TO_COST_RATIO[mode],
    )


def _format_pipeline_cli_json(invocation) -> dict:
    """Build JSON output for the pipeline CLI command."""
    classification = invocation.classification
    summary = invocation.summary
    return {
        "classification": {
            "request": classification.request,
            "work_type": classification.work_type.value,
            "stage_order": list(classification.stage_order),
            "execution_mode": (
                classification.execution_mode.value
                if classification.execution_mode is not None
                else None
            ),
            "required_execution_mode": (
                classification.required_execution_mode.value
                if classification.required_execution_mode is not None
                else None
            ),
            "approval_gate": classification.approval_gate,
            "stop_after_stage": classification.stop_after_stage,
            "allow_single_agent_fallback": classification.allow_single_agent_fallback,
            "blocked_reason": classification.blocked_reason,
            "reason": classification.reason,
        },
        "pipeline_result": invocation.pipeline_result.to_dict(),
        "summary": {
            "work_type": summary.work_type.value,
            "execution_mode": summary.execution_mode,
            "required_execution_mode": summary.required_execution_mode,
            "stage_order": list(summary.stage_order),
            "files_changed": list(summary.files_changed),
            "blockers": summary.blockers,
            "blocked_reason": summary.blocked_reason,
            "retries_used": summary.retries_used,
            "final_status": summary.final_status.value,
            "next_action": summary.next_action,
        },
        "rendered_summary": invocation.rendered_summary,
    }


def cmd_pipeline(args: argparse.Namespace) -> int:
    """Run the mstack-pipeline adapter flow through the CLI."""
    dispatch_result = _build_pipeline_router_result(args.mode)
    project_dir = Path.cwd()
    preset = resolve_preset(project_dir, None, None, None)
    external_executor = None
    if args.external_executor == "codex":
        external_executor = build_codex_exec_parallel_executor()
        if external_executor is None:
            print("[mstack] ❌ codex CLI not found for --external-executor codex", file=sys.stderr)
            return 1

    executor_capabilities = set(detect_parallel_executor_capabilities(
        ImplementRecipeContext(
            project_dir=project_dir,
            request=args.request,
            lang=preset.lang,
        )
    ))
    if external_executor is not None:
        executor_capabilities.update(external_executor.capabilities)
    payload = PipelineRequestClassifierInput(
        request=args.request,
        dispatch_result=dispatch_result,
        approval_gate_requested=args.require_approval,
        allow_single_agent_fallback=args.allow_single_agent_fallback,
        executor_capabilities=frozenset(executor_capabilities),
    )
    stage_runner = build_stage_runner(
        project_dir,
        args.request,
        dispatch_result=dispatch_result,
        generic_implement_backend=build_generic_implement_backend(args.generic_implement),
        parallel_executor=external_executor,
        executor_capabilities=frozenset(executor_capabilities),
        fail_stage=args.mock_fail_stage,
        fail_until=args.mock_fail_until,
    )
    invocation = run_pipeline_request(
        payload,
        stage_runner,
        next_action=args.next_action,
    )

    if args.json:
        print(json.dumps(_format_pipeline_cli_json(invocation), ensure_ascii=False, indent=2))
    else:
        print(invocation.rendered_summary)

    return 0 if invocation.pipeline_result.final_status in {StageStatus.PASSED, StageStatus.PENDING} else 1


# ═══════════════════════════════════════════════════════
#  UPGRADE
# ═══════════════════════════════════════════════════════

def cmd_upgrade(args: argparse.Namespace) -> int:
    """mstack 자체 업그레이드 (GitHub에서 최신 pull)"""
    import subprocess

    if args.check_only:
        print(f"[mstack] Current version: {__version__}")
        print("[mstack] Check-only mode. No changes made.")
        return 0

    try:
        subprocess.run(
            ["git", "-C", str(MSTACK_ROOT), "pull", "--rebase"],
            check=True
        )
        print(f"[mstack] ✅ Updated to latest version")
    except subprocess.CalledProcessError:
        print("[mstack] ❌ Upgrade failed. Check network connection.")
        return 1

    return 0


# ═══════════════════════════════════════════════════════
#  DOCTOR
# ═══════════════════════════════════════════════════════

def cmd_doctor(args: argparse.Namespace) -> int:
    """환경 진단: Python, Git, Claude CLI, 프로젝트 상태 점검"""
    cwd = Path.cwd()
    results = run_all_checks(cwd, __version__)

    if args.json:
        print(json.dumps(format_results_json(results), indent=2, ensure_ascii=False))
    else:
        print(format_results(results, cwd))

    has_failure = any(r.status.value == "fail" for r in results)
    return 1 if has_failure else 0


# ═══════════════════════════════════════════════════════
#  ARGPARSE
# ═══════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mstack",
        description="MACHO-STACK: Claude Code SDLC toolkit (Gstack × CCAT)",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="Initialize project with skills, hooks, CLAUDE.md")
    p_init.add_argument("--preset", help="Preset name (python/ts/go/rust/hvdc)")
    p_init.add_argument("--lang", help="Language override")
    p_init.add_argument("--hooks", choices=["basic", "extended"], default="basic",
                        help="Hook level (basic=2, extended=6)")
    p_init.add_argument("--force", action="store_true", help="Overwrite existing files")
    p_init.add_argument("--dry-run", action="store_true", help="Show plan without creating files")
    p_init.add_argument("--no-lazy", action="store_true",
                        help="Disable lazy skill loading (embed full skills in CLAUDE.md)")
    p_init.set_defaults(func=cmd_init)

    # cost
    p_cost = sub.add_parser("cost", help="View cost report or dashboard")
    p_cost.add_argument("--dashboard", action="store_true", help="Generate HTML dashboard")
    p_cost.add_argument("--threshold", type=float, help="Cost alert threshold (USD)")
    p_cost.add_argument("--output", help="Dashboard output path")
    p_cost.add_argument("--no-open", action="store_true", help="Don't auto-open browser")
    p_cost.set_defaults(func=cmd_cost)

    # check
    p_check = sub.add_parser("check", help="Drift detection + Agent Teams router")
    p_check.add_argument("--files", nargs="*", help="Changed files (auto-detect from git if omitted)")
    p_check.add_argument("--apply", action="store_true",
                         help="Apply recommendation: update CLAUDE.md banner + session.json + settings.json")
    p_check.set_defaults(func=cmd_check)

    # install-codex
    p_install_codex = sub.add_parser("install-codex", help="Install packaged Codex skills into ~/.codex/skills")
    p_install_codex.add_argument(
        "--target",
        default=str(Path.home() / ".codex" / "skills"),
        help="Codex skills target directory",
    )
    p_install_codex.add_argument("--force", action="store_true", help="Overwrite existing managed MStack skill dirs")
    p_install_codex.add_argument("--dry-run", action="store_true", help="Show planned installs without copying files")
    p_install_codex.set_defaults(func=cmd_install_codex)

    # room-log
    p_room_log = sub.add_parser("room-log", help="Append or read room-based group logs")
    room_sub = p_room_log.add_subparsers(dest="room_log_command")
    p_room_log.set_defaults(func=lambda args, parser=p_room_log: _cmd_room_log_help(parser))

    p_room_log_bind = room_sub.add_parser("bind", help="Create or bind the active room for later hook/appends")
    p_room_log_bind.add_argument("--room-name", required=True, help="Display room name")
    p_room_log_bind.add_argument("--room-slug", help="Stable room slug override")
    p_room_log_bind.add_argument("--json", action="store_true", help="Output binding info as JSON")
    p_room_log_bind.set_defaults(func=cmd_room_log_bind)

    p_room_log_append = room_sub.add_parser("append", help="Append one room log event")
    p_room_log_append.add_argument("--room-name", help="Display room name")
    p_room_log_append.add_argument("--room-slug", help="Stable room slug")
    p_room_log_append.add_argument("--event-type", required=True, help="Event type to record")
    p_room_log_append.add_argument("--sender", required=True, help="Message sender")
    p_room_log_append.add_argument("--message", required=True, help="Message or summary text")
    p_room_log_append.add_argument("--timestamp", help="Optional ISO timestamp override")
    p_room_log_append.add_argument("--session-id", help="Optional session id")
    p_room_log_append.add_argument("--hook-event", help="Whitelisted metadata: hook event")
    p_room_log_append.add_argument("--tool-name", help="Whitelisted metadata: tool name")
    p_room_log_append.add_argument("--stage", help="Whitelisted metadata: stage")
    p_room_log_append.add_argument("--status", help="Whitelisted metadata: status")
    p_room_log_append.add_argument("--agent-id", help="Whitelisted metadata: agent id")
    p_room_log_append.set_defaults(func=cmd_room_log_append)

    p_room_log_tail = room_sub.add_parser("tail", help="Read recent room log entries")
    p_room_log_tail.add_argument("--room-name", help="Display room name")
    p_room_log_tail.add_argument("--room-slug", help="Stable room slug")
    p_room_log_tail.add_argument("--limit", type=int, default=5, help="Max entries to return")
    p_room_log_tail.add_argument("--max-chars", type=int, default=800, help="Max total message chars")
    p_room_log_tail.add_argument("--json", action="store_true", help="Output as JSON")
    p_room_log_tail.set_defaults(func=cmd_room_log_tail)

    # pipeline
    p_pipeline = sub.add_parser("pipeline", help="Run the mstack-pipeline adapter flow")
    p_pipeline.add_argument("request", help="Natural-language pipeline request")
    p_pipeline.add_argument(
        "--mode",
        choices=["single", "subagent", "agent_teams"],
        help="Optional execution mode override",
    )
    p_pipeline.add_argument(
        "--allow-single-agent-fallback",
        action="store_true",
        help="Explicitly approve single-agent fallback when required delegation is unavailable",
    )
    p_pipeline.add_argument(
        "--external-executor",
        choices=["codex"],
        help="Enable an external parallel executor backend for generic free-form implementation",
    )
    p_pipeline.add_argument(
        "--require-approval",
        action="store_true",
        help="Request an approval gate in the classified pipeline flow",
    )
    p_pipeline.add_argument(
        "--generic-implement",
        choices=["none", "notes"],
        default="none",
        help="Optional generic implement backend when no deterministic recipe matches",
    )
    p_pipeline.add_argument(
        "--mock-fail-stage",
        choices=["plan", "implement", "review", "qa", "ship", "retro", "investigate"],
        help="Testing hook: force a stage to fail in the injected stage runner",
    )
    p_pipeline.add_argument(
        "--mock-fail-until",
        type=int,
        default=0,
        help="Testing hook: for qa, fail this many times before passing",
    )
    p_pipeline.add_argument(
        "--next-action",
        help="Optional next-action override for the final summary",
    )
    p_pipeline.add_argument("--json", action="store_true", help="Output pipeline result as JSON")
    p_pipeline.set_defaults(func=cmd_pipeline)

    # doctor
    p_doctor = sub.add_parser("doctor", help="Check environment and project health")
    p_doctor.add_argument("--json", action="store_true", help="Output as JSON")
    p_doctor.set_defaults(func=cmd_doctor)

    # upgrade
    p_upgrade = sub.add_parser("upgrade", help="Self-update from GitHub")
    p_upgrade.add_argument("--check-only", action="store_true", help="Check for updates only")
    p_upgrade.set_defaults(func=cmd_upgrade)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
