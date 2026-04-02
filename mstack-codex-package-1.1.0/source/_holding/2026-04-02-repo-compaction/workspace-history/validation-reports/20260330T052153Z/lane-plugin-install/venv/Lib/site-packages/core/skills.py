"""core/skills.py — 스킬 파일 배포 + CLAUDE.md용 Lazy Index 생성"""
from __future__ import annotations
from pathlib import Path
from types import MappingProxyType
import shutil

from .assets import asset_dir

# ── 스킬 목록 (8종) ──────────────────────────────────

SKILL_INDEX: MappingProxyType = MappingProxyType({
    "plan": {
        "persona": "CEO + Engineering Manager",
        "description": "아키텍처 설계 리뷰. 요구사항 → 시스템 설계 → 인터페이스 정의",
        "trigger": "/plan",
    },
    "review": {
        "persona": "Senior Code Reviewer",
        "description": "보안/성능/품질 3축 코드 리뷰",
        "trigger": "/review",
    },
    "ship": {
        "persona": "Release Manager",
        "description": "lint→test→build→deploy 배포 체크리스트",
        "trigger": "/ship",
    },
    "qa": {
        "persona": "QA Engineer",
        "description": "자동 테스트 실행 + 결과 분석 + 커버리지 확인",
        "trigger": "/qa",
    },
    "investigate": {
        "persona": "Senior Debugger",
        "description": "버그 재현 → 격리 → 근본 원인 분석",
        "trigger": "/investigate",
    },
    "retro": {
        "persona": "Scrum Master",
        "description": "최근 7일 커밋 로그 분석 → 주간 회고 보고서",
        "trigger": "/retro",
    },
    "careful": {
        "persona": "Safety Guard",
        "description": "파괴적 명령(rm -rf, force push, DROP TABLE) 실행 전 경고",
        "trigger": "/careful",
    },
    "dispatch": {
        "persona": "Orchestrator",
        "description": "작업 분석 → SINGLE/SUBAGENT/AGENT_TEAMS 자동 추천 + 팀 구성 + 실행",
        "trigger": "/dispatch",
    },
})

SKILL_NAMES = tuple(SKILL_INDEX.keys())


def deploy_skills(source_dir: Path, target_dir: Path,
                  skill_names: list[str] | None = None) -> list[Path]:
    """스킬 파일을 target 디렉토리에 복사한다.

    source_dir 구조: source_dir/{name}/SKILL.md (nested)
    target_dir 구조: target_dir/{name}.md (flat)

    Args:
        source_dir: mstack 패키지 내 skills/ 디렉토리
        target_dir: 프로젝트 .claude/skills/mstack/ 디렉토리
        skill_names: 배포할 스킬 목록 (None이면 전체)

    Returns:
        생성된 파일 경로 리스트
    """
    names = skill_names or SKILL_NAMES
    target_dir.mkdir(parents=True, exist_ok=True)
    created = []

    for name in names:
        # 실제 디렉토리 구조: skills/{name}/SKILL.md
        src = source_dir / name / "SKILL.md"
        dst = target_dir / f"{name}.md"
        if not src.exists():
            raise FileNotFoundError(f"Skill source not found: {src}")
        shutil.copy2(src, dst)
        created.append(dst)

    return created


def packaged_skills_dir() -> Path:
    """Return the packaged classic skills directory."""
    return asset_dir("skills")


def generate_lazy_index(skill_names: list[str] | None = None) -> str:
    """CLAUDE.md용 Lazy Skill Index를 생성한다.

    Full content 대신 1줄 요약만 포함하여 토큰 절감.
    """
    names = skill_names or SKILL_NAMES
    lines = ["## Available Skills (Lazy Index)", ""]
    lines.append("| Skill | Trigger | Persona | Description |")
    lines.append("|---|---|---|---|")

    for name in names:
        info = SKILL_INDEX[name]
        lines.append(
            f"| {name} | `{info['trigger']}` "
            f"| {info['persona']} | {info['description']} |"
        )

    lines.append("")
    lines.append("> Full skill definitions: `.claude/skills/mstack/*.md`")
    lines.append("> Claude will load the full skill content when a trigger command is used.")
    return "\n".join(lines)


def generate_inline_skills(skill_names: list[str] | None = None) -> str:
    """CLAUDE.md용 인라인 스킬 설명을 생성한다 (lazy_skills=False 시 사용).

    각 스킬별 한 단락씩 embed하여 lazy index 대비 충분한 토큰 차이를 만든다.
    """
    names = skill_names or SKILL_NAMES
    lines = ["## Skills (Full Index)", ""]

    for name in names:
        info = SKILL_INDEX[name]
        lines.append(f"### `{info['trigger']}` — {name}")
        lines.append("")
        lines.append(f"**Persona**: {info['persona']}")
        lines.append("")
        lines.append(f"**Description**: {info['description']}")
        lines.append("")
        lines.append(f"**Usage**: Type `{info['trigger']}` in Claude Code to invoke this skill.")
        lines.append(f"The skill will guide you through a structured {name} workflow.")
        lines.append(f"Full skill definition: `.claude/skills/mstack/{name}.md`")
        lines.append("")

    return "\n".join(lines)


def measure_skill_tokens(skills_dir: Path) -> dict[str, int]:
    """각 스킬 파일의 대략적 토큰 수를 측정한다.

    근사치: chars / 4 (영문 기준)
    """
    result = {}
    for md in sorted(skills_dir.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        result[md.stem] = len(text) // 4
    return result
