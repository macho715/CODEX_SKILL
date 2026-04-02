"""tests/test_config.py — core/config.py 단위 테스트"""
import pytest
from pathlib import Path
from core.config import detect_lang, scan_dirs, load_preset, resolve_preset
from core.types import Lang


def test_detect_python(project_dir):
    assert detect_lang(project_dir) == Lang.PYTHON


def test_detect_ts(tmp_path):
    (tmp_path / "package.json").write_text("{}")
    assert detect_lang(tmp_path) == Lang.TS


def test_detect_unknown(tmp_path):
    assert detect_lang(tmp_path) == Lang.UNKNOWN


def test_scan_dirs(project_dir):
    dirs = scan_dirs(project_dir)
    assert "src" in dirs
    assert "tests" in dirs
    assert ".git" not in dirs


def test_load_builtin_preset():
    preset = load_preset("python")
    assert preset.name == "python"
    assert preset.lang == Lang.PYTHON
    assert "pytest" in preset.test_cmd


def test_resolve_with_preset(project_dir):
    preset = resolve_preset(project_dir, "python", None, None)
    assert preset.name == "python"


def test_resolve_auto_detect(project_dir):
    preset = resolve_preset(project_dir, None, None, None)
    assert preset.lang == Lang.PYTHON


def test_builtin_presets_immutable():
    """v1.2: BUILTIN_PRESETS가 외부 변이로부터 보호되는지 확인"""
    from core.config import BUILTIN_PRESETS
    with pytest.raises(TypeError):
        BUILTIN_PRESETS["python"] = {"hacked": True}
    with pytest.raises(TypeError):
        BUILTIN_PRESETS["python"]["name"] = "hacked"


# ── 미커버 라인 보강 (v1.4) ──────────────────────────────


def test_load_preset_unknown_raises():
    """존재하지 않는 프리셋 이름이면 ValueError 발생 (L154-155)."""
    with pytest.raises(ValueError, match="Unknown preset"):
        load_preset("nonexistent_preset_xyz")


def test_resolve_preset_lang_override(project_dir):
    """lang_override가 주어지면 해당 프리셋을 로드 (L174)."""
    preset = resolve_preset(project_dir, None, "python", None)
    assert preset.name == "python"
    assert preset.lang == Lang.PYTHON
