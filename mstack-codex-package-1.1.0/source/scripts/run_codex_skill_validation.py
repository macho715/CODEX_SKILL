"""Parallel end-to-end validation runner for MStack Codex skills and plugin packaging.

This script builds the wheel once, creates isolated virtual environments, runs
three validation lanes in parallel, and writes both JSON and Markdown reports.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
import venv


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT_ROOT = REPO_ROOT / "skills-workspace" / "validation-reports"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


@dataclass
class LaneResult:
    """Structured result for one validation lane."""

    name: str
    status: str
    duration_sec: float
    commands: list[str] = field(default_factory=list)
    artifacts: dict[str, str] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)
    error: str | None = None


def _venv_python(venv_dir: Path) -> Path:
    if sys.platform == "win32":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def _build_wheel(run_root: Path) -> Path:
    wheelhouse = run_root / "wheelhouse"
    wheelhouse.mkdir(parents=True, exist_ok=True)
    build = _run(
        [sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", str(wheelhouse)],
        cwd=REPO_ROOT,
        timeout=600,
    )
    if build.returncode != 0:
        raise RuntimeError(build.stderr or build.stdout or "wheel build failed")

    wheels = sorted(wheelhouse.glob("mstack-*.whl"))
    if not wheels:
        raise RuntimeError("wheel build produced no mstack wheel")
    return wheels[-1]


def _create_venv(venv_dir: Path) -> Path:
    builder = venv.EnvBuilder(with_pip=True, clear=True)
    builder.create(venv_dir)
    python = _venv_python(venv_dir)
    if not python.exists():
        raise RuntimeError(f"venv python not found: {python}")
    return python


def _install_wheel(venv_python: Path, wheel_path: Path) -> str:
    install = _run(
        [str(venv_python), "-m", "pip", "install", str(wheel_path)],
        cwd=REPO_ROOT,
        timeout=600,
    )
    if install.returncode != 0:
        raise RuntimeError(install.stderr or install.stdout or "pip install failed")
    return install.stdout.strip()


def _validate_direct_install(target: Path) -> list[str]:
    expected = {
        "mstack-careful",
        "mstack-dispatch",
        "mstack-investigate",
        "mstack-pipeline",
        "mstack-pipeline-coordinator",
        "mstack-plan",
        "mstack-qa",
        "mstack-retro",
        "mstack-review",
        "mstack-ship",
    }
    found = {path.name for path in target.iterdir() if path.is_dir()}
    if found != expected:
        raise RuntimeError(f"direct install mismatch: found={sorted(found)}")

    checks: list[str] = []
    if not (target / "MSTACK_SKILL_GUIDE.md").exists():
        raise RuntimeError("missing MSTACK_SKILL_GUIDE.md in direct install target")
    checks.append("validated:direct-guide")
    for name in sorted(expected):
        skill_dir = target / name
        if not (skill_dir / "SKILL.md").exists():
            raise RuntimeError(f"missing SKILL.md for {name}")
        if not (skill_dir / "agents" / "openai.yaml").exists():
            raise RuntimeError(f"missing openai.yaml for {name}")
        if not (skill_dir / ".mstack-install.json").exists():
            raise RuntimeError(f"missing managed install marker for {name}")
        checks.append(f"validated:{name}")
    return checks


def _validate_plugin_install(plugin_root: Path, marketplace_path: Path) -> list[str]:
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    if not manifest_path.exists():
        raise RuntimeError("plugin manifest missing")
    if not (plugin_root / "MSTACK_SKILL_GUIDE.md").exists():
        raise RuntimeError("plugin guide missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("name") != "mstack-codex":
        raise RuntimeError(f"unexpected plugin name: {manifest.get('name')}")
    if manifest.get("skills") not in {"./skills", "./skills/"}:
        raise RuntimeError(f"unexpected skills path: {manifest.get('skills')}")

    skills_root = plugin_root / "skills"
    skill_dirs = sorted(path.name for path in skills_root.iterdir() if path.is_dir())
    if skill_dirs != [
        "careful",
        "dispatch",
        "investigate",
        "pipeline",
        "pipeline-coordinator",
        "plan",
        "qa",
        "retro",
        "review",
        "ship",
    ]:
        raise RuntimeError(f"plugin skill tree mismatch: {skill_dirs}")

    if not (plugin_root / ".mstack-plugin-install.json").exists():
        raise RuntimeError("plugin managed install marker missing")
    if not marketplace_path.exists():
        raise RuntimeError("marketplace file missing")

    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    plugin_entry = next(
        (item for item in marketplace.get("plugins", []) if item.get("name") == "mstack-codex"),
        None,
    )
    if plugin_entry is None:
        raise RuntimeError("mstack-codex entry missing from marketplace")
    source_path = plugin_entry.get("source", {}).get("path")
    if source_path != "./plugins/mstack-codex":
        raise RuntimeError(f"unexpected marketplace source path: {source_path}")

    return [
        "validated:plugin-guide",
        "validated:plugin-manifest",
        "validated:plugin-skill-tree",
        "validated:plugin-managed-marker",
        "validated:marketplace-entry",
    ]


def _lane_direct_install(wheel_path: Path, lane_root: Path) -> LaneResult:
    start = time.time()
    commands: list[str] = []
    artifacts: dict[str, str] = {}
    details: list[str] = []

    venv_dir = lane_root / "venv"
    target_dir = lane_root / "codex-skills"
    venv_python = _create_venv(venv_dir)
    commands.append(f"{venv_python} -m pip install {wheel_path}")
    _install_wheel(venv_python, wheel_path)

    install_cmd = [str(venv_python), "-m", "mstack", "install-codex", "--target", str(target_dir)]
    commands.append(" ".join(install_cmd))
    install = _run(install_cmd, cwd=REPO_ROOT, timeout=300)
    if install.returncode != 0:
        raise RuntimeError(install.stderr or install.stdout or "install-codex failed")

    details.extend(_validate_direct_install(target_dir))
    artifacts["venv"] = str(venv_dir)
    artifacts["target_dir"] = str(target_dir)
    artifacts["stdout"] = install.stdout.strip()
    return LaneResult(
        name="lane-direct-install",
        status="passed",
        duration_sec=round(time.time() - start, 2),
        commands=commands,
        artifacts=artifacts,
        details=details,
    )


def _lane_plugin_install(wheel_path: Path, lane_root: Path) -> LaneResult:
    start = time.time()
    commands: list[str] = []
    artifacts: dict[str, str] = {}
    details: list[str] = []

    venv_dir = lane_root / "venv"
    plugin_root = lane_root / "plugins" / "mstack-codex"
    marketplace_path = lane_root / ".agents" / "plugins" / "marketplace.json"
    venv_python = _create_venv(venv_dir)
    commands.append(f"{venv_python} -m pip install {wheel_path}")
    _install_wheel(venv_python, wheel_path)

    install_cmd = [
        str(venv_python),
        "-m",
        "mstack",
        "install-codex-plugin",
        "--target",
        str(plugin_root),
        "--with-marketplace",
        "--marketplace-path",
        str(marketplace_path),
    ]
    commands.append(" ".join(install_cmd))
    install = _run(install_cmd, cwd=REPO_ROOT, timeout=300)
    if install.returncode != 0:
        raise RuntimeError(install.stderr or install.stdout or "install-codex-plugin failed")

    details.extend(_validate_plugin_install(plugin_root, marketplace_path))
    artifacts["venv"] = str(venv_dir)
    artifacts["plugin_root"] = str(plugin_root)
    artifacts["marketplace_path"] = str(marketplace_path)
    artifacts["stdout"] = install.stdout.strip()
    return LaneResult(
        name="lane-plugin-install",
        status="passed",
        duration_sec=round(time.time() - start, 2),
        commands=commands,
        artifacts=artifacts,
        details=details,
    )


def _lane_runtime_smoke(wheel_path: Path, lane_root: Path) -> LaneResult:
    start = time.time()
    commands: list[str] = []
    artifacts: dict[str, str] = {}
    details: list[str] = []

    venv_dir = lane_root / "venv"
    output_json = lane_root / "runtime-smoke.json"
    venv_python = _create_venv(venv_dir)
    commands.append(f"{venv_python} -m pip install {wheel_path}")
    _install_wheel(venv_python, wheel_path)

    env = os.environ.copy()
    script = REPO_ROOT / "scripts" / "codex_runtime_smoke.py"
    smoke_cmd = [
        str(venv_python),
        str(script),
        "--repo",
        str(REPO_ROOT),
        "--keep-artifacts",
        "--skip-git-repo-check",
        "--timeout",
        "240",
    ]
    commands.append(" ".join(smoke_cmd))
    smoke = _run(smoke_cmd, cwd=REPO_ROOT, env=env, timeout=1800)
    if smoke.returncode != 0:
        raise RuntimeError(smoke.stderr or smoke.stdout or "runtime smoke failed")

    output_json.write_text(smoke.stdout, encoding="utf-8")
    summary = json.loads(smoke.stdout)
    if summary.get("ok") is not True:
        raise RuntimeError(f"runtime smoke reported failure: {summary}")
    if len(summary.get("results", [])) != 10:
        raise RuntimeError("runtime smoke did not cover 10 skills")
    if not all(entry.get("passed") for entry in summary["results"]):
        raise RuntimeError("runtime smoke has failing skill cases")

    details.append("validated:runtime-smoke-ok")
    details.append("validated:runtime-skill-count=10")
    details.extend(f"validated:{entry['name']}" for entry in summary["results"])
    artifacts["venv"] = str(venv_dir)
    artifacts["summary_json"] = str(output_json)
    if "persisted_output_dir" in summary:
        artifacts["persisted_output_dir"] = str(summary["persisted_output_dir"])
    return LaneResult(
        name="lane-runtime-smoke",
        status="passed",
        duration_sec=round(time.time() - start, 2),
        commands=commands,
        artifacts=artifacts,
        details=details,
    )


def _run_lane(name: str, lane_fn, wheel_path: Path, lane_root: Path) -> LaneResult:
    start = time.time()
    lane_root.mkdir(parents=True, exist_ok=True)
    try:
        return lane_fn(wheel_path, lane_root)
    except Exception as exc:  # pragma: no cover - used for operational reporting
        return LaneResult(
            name=name,
            status="failed",
            duration_sec=round(time.time() - start, 2),
            error=f"{exc}\n{traceback.format_exc()}",
        )


def _render_report(summary: dict[str, object]) -> str:
    lines = [
        "# MStack Codex Skill Validation Report",
        "",
        f"- Generated: `{summary['generated_at']}`",
        f"- Repo: `{summary['repo_root']}`",
        f"- Overall Status: `{summary['overall_status']}`",
        f"- Automatic Patch Action: `{summary['automatic_patch_action']}`",
        "",
        "## Lanes",
        "",
    ]

    for lane in summary["lanes"]:
        lines.append(f"### {lane['name']}")
        lines.append("")
        lines.append(f"- Status: `{lane['status']}`")
        lines.append(f"- Duration: `{lane['duration_sec']}s`")
        if lane.get("details"):
            lines.append(f"- Checks: `{', '.join(lane['details'])}`")
        if lane.get("artifacts"):
            for key, value in lane["artifacts"].items():
                lines.append(f"- {key}: `{value}`")
        if lane.get("error"):
            lines.append("- Error:")
            lines.append("```text")
            lines.append(str(lane["error"]).strip())
            lines.append("```")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> int:
    report_root = DEFAULT_REPORT_ROOT / TIMESTAMP
    report_root.mkdir(parents=True, exist_ok=True)

    wheel_path = _build_wheel(report_root)
    lanes = {
        "lane-direct-install": _lane_direct_install,
        "lane-plugin-install": _lane_plugin_install,
        "lane-runtime-smoke": _lane_runtime_smoke,
    }

    results: list[LaneResult] = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_map = {
            executor.submit(_run_lane, name, lane_fn, wheel_path, report_root / name): name
            for name, lane_fn in lanes.items()
        }
        for future in as_completed(future_map):
            results.append(future.result())

    results.sort(key=lambda item: item.name)
    overall_status = "passed" if all(result.status == "passed" for result in results) else "failed"
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(REPO_ROOT),
        "wheel_path": str(wheel_path),
        "overall_status": overall_status,
        "automatic_patch_action": "none-required" if overall_status == "passed" else "manual-follow-up-required",
        "lanes": [asdict(result) for result in results],
    }

    json_path = report_root / "validation-summary.json"
    md_path = report_root / "validation-summary.md"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_report(summary), encoding="utf-8")

    print(json.dumps({"overall_status": overall_status, "report_dir": str(report_root)}, ensure_ascii=False))
    return 0 if overall_status == "passed" else 1


if __name__ == "__main__":
    sys.exit(main())
