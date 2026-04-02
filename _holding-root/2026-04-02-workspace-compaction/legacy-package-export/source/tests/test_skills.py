"""tests/test_skills.py — core/skills.py 단위 테스트"""
import pytest
from pathlib import Path
from core.skills import (
    SKILL_NAMES,
    SKILL_INDEX,
    deploy_skills,
    generate_lazy_index,
    measure_skill_tokens,
)


def test_skill_names_count():
    assert len(SKILL_NAMES) == len(SKILL_INDEX)


def test_skill_index_has_all_skills():
    for name in SKILL_NAMES:
        assert name in SKILL_INDEX
        assert "persona" in SKILL_INDEX[name]
        assert "trigger" in SKILL_INDEX[name]
        assert "description" in SKILL_INDEX[name]


def test_deploy_skills(tmp_path):
    """실제 skills/ 디렉토리에서 8개 파일 복사 검증"""
    import sys
    ccat_root = Path(__file__).parent.parent
    skills_src = ccat_root / "skills"

    target = tmp_path / "output_skills"
    created = deploy_skills(skills_src, target)

    assert len(created) == 8
    for path in created:
        assert path.exists()
        assert path.suffix == ".md"


def test_generate_lazy_index_contains_all_skills():
    index = generate_lazy_index()
    for name in SKILL_NAMES:
        assert name in index

    # 테이블 헤더 포함 확인
    assert "| Skill |" in index
    assert "Trigger" in index


def test_generate_lazy_index_has_triggers():
    index = generate_lazy_index()
    for name, info in SKILL_INDEX.items():
        assert info["trigger"] in index


def test_measure_skill_tokens(tmp_path):
    """토큰 측정 - 임시 스킬 파일 생성 후 검증"""
    (tmp_path / "plan.md").write_text("A" * 400, encoding="utf-8")
    (tmp_path / "review.md").write_text("B" * 800, encoding="utf-8")

    result = measure_skill_tokens(tmp_path)

    assert "plan" in result
    assert "review" in result
    assert result["plan"] == 100   # 400 // 4
    assert result["review"] == 200  # 800 // 4


# ── 미커버 라인 보강 (v1.4) ──────────────────────────────


def test_deploy_skills_missing_source_raises(tmp_path):
    """스킬 소스 파일이 없으면 FileNotFoundError 발생 (L79)."""
    empty_src = tmp_path / "empty_skills"
    empty_src.mkdir()
    # SKILL_NAMES에 해당하는 디렉토리가 없으므로 에러
    target = tmp_path / "output"
    with pytest.raises(FileNotFoundError, match="Skill source not found"):
        deploy_skills(empty_src, target)
