"""core/config.py — 프리셋 로드, 언어 자동 감지, 프로젝트 스캔"""
from __future__ import annotations
from pathlib import Path
from types import MappingProxyType
from typing import Any
import json
from .assets import asset_dir
from .types import Preset, Lang


# ── 내장 프리셋 (presets/*.json 없을 때 fallback) ──────
# v1.2: MappingProxyType으로 외부 변이 방지 (cost.P 오염 사례 교훈)

def _freeze_preset(d: dict[str, Any]) -> MappingProxyType[str, Any]:
    """프리셋 dict를 재귀적으로 불변화한다."""
    frozen: dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, dict):
            frozen[k] = MappingProxyType(v)
        elif isinstance(v, list):
            frozen[k] = tuple(v)
        else:
            frozen[k] = v
    return MappingProxyType(frozen)


BUILTIN_PRESETS: MappingProxyType = MappingProxyType({
    "python": _freeze_preset({
        "name": "python", "lang": "python",
        "test_cmd": "pytest tests/ -x",
        "lint_cmd": "ruff check .",
        "type_cmd": "mypy --strict .",
        "rules": ["Always use type hints", "Follow PEP 8"],
        "permissions": {"Bash": True, "Edit": True, "Write": True},
        "hooks_level": "basic",
        "custom_skills": [],
        "domain_terms": {},
        "fanr_rules": [],
    }),
    "ts": _freeze_preset({
        "name": "ts", "lang": "ts",
        "test_cmd": "npm test",
        "lint_cmd": "npx eslint .",
        "type_cmd": "npx tsc --noEmit",
        "rules": ["Strict TypeScript, no any"],
        "permissions": {"Bash": True, "Edit": True, "Write": True},
        "hooks_level": "basic",
        "custom_skills": [],
        "domain_terms": {},
        "fanr_rules": [],
    }),
    "go": _freeze_preset({
        "name": "go", "lang": "go",
        "test_cmd": "go test ./...",
        "lint_cmd": "golangci-lint run",
        "type_cmd": "",
        "rules": ["gofmt / golangci-lint / error wrapping 필수"],
        "permissions": {"Bash": True, "Edit": True, "Write": True},
        "hooks_level": "basic",
        "custom_skills": [],
        "domain_terms": {},
        "fanr_rules": [],
    }),
    "rust": _freeze_preset({
        "name": "rust", "lang": "rust",
        "test_cmd": "cargo test",
        "lint_cmd": "cargo clippy -- -D warnings",
        "type_cmd": "",
        "rules": ["cargo fmt / clippy clean / unsafe 최소화"],
        "permissions": {"Bash": True, "Edit": True, "Write": True},
        "hooks_level": "basic",
        "custom_skills": [],
        "domain_terms": {},
        "fanr_rules": [],
    }),
    "unknown": _freeze_preset({
        "name": "unknown", "lang": "unknown",
        "test_cmd": "",
        "lint_cmd": "",
        "type_cmd": "",
        "rules": [],
        "permissions": {},
        "hooks_level": "basic",
        "custom_skills": [],
        "domain_terms": {},
        "fanr_rules": [],
    }),
})


def detect_lang(project_dir: Path) -> Lang:
    """프로젝트 디렉토리에서 언어를 자동 감지한다.

    우선순위: pyproject.toml > requirements.txt > setup.py > package.json >
              tsconfig.json > go.mod > Cargo.toml
    """
    markers = [
        ("pyproject.toml", Lang.PYTHON),
        ("requirements.txt", Lang.PYTHON),
        ("setup.py", Lang.PYTHON),
        ("package.json", Lang.TS),
        ("tsconfig.json", Lang.TS),
        ("go.mod", Lang.GO),
        ("Cargo.toml", Lang.RUST),
    ]
    for marker, lang in markers:
        if (project_dir / marker).exists():
            return lang
    return Lang.UNKNOWN


def scan_dirs(project_dir: Path) -> list[str]:
    """프로젝트 최상위 디렉토리 목록을 반환한다.

    .git, node_modules, __pycache__, .venv 등은 제외.
    """
    ignore = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        ".mypy_cache", ".ruff_cache", ".pytest_cache", "dist", "build",
    }
    return sorted([
        d.name for d in project_dir.iterdir()
        if d.is_dir() and d.name not in ignore and not d.name.startswith(".")
    ])


def load_preset(name: str, presets_dir: Path | None = None) -> Preset:
    """프리셋을 로드한다. JSON 파일 우선, 없으면 내장 fallback.

    Args:
        name: 프리셋 이름 (python, ts, hvdc, ...)
        presets_dir: presets/ 디렉토리 경로 (None이면 내장만)

    Raises:
        ValueError: 프리셋을 찾을 수 없을 때
    """
    preset_root = presets_dir or asset_dir("presets")

    # 1) JSON 파일 우선
    json_path = preset_root / f"{name}.json"
    if json_path.exists():
        return Preset.from_json(json_path)

    # 2) 내장 fallback
    if name in BUILTIN_PRESETS:
        # MappingProxyType → 일반 dict로 변환하여 Preset 생성
        data = dict(BUILTIN_PRESETS[name])
        # frozen된 내부 값들도 mutable로 복원
        for k, v in data.items():
            if isinstance(v, MappingProxyType):
                data[k] = dict(v)
            elif isinstance(v, tuple) and k in ("rules", "custom_skills", "fanr_rules"):
                data[k] = list(v)
        data["lang"] = Lang(data["lang"])
        return Preset(**data)

    available = list(BUILTIN_PRESETS.keys())
    raise ValueError(f"Unknown preset: {name}. Available: {available}")


def resolve_preset(
    project_dir: Path,
    preset_name: str | None,
    lang_override: str | None,
    presets_dir: Path | None,
) -> Preset:
    """프리셋을 최종 결정한다.

    1. --preset 지정 시 해당 프리셋
    2. --lang 지정 시 해당 언어 프리셋
    3. 둘 다 없으면 자동 감지
    """
    if preset_name:
        return load_preset(preset_name, presets_dir)

    if lang_override:
        return load_preset(lang_override, presets_dir)

    lang = detect_lang(project_dir)
    return load_preset(lang.value, presets_dir)
