"""tests/test_context_size.py — v1.1 토큰 절감 벤치마크"""
from core.claude_md import generate_claude_md, measure_token_count
from core.config import load_preset


def test_lazy_vs_inline_token_reduction():
    """Lazy Index가 inline 대비 30%+ 토큰 절감하는지 검증"""
    preset = load_preset("python")

    # v1.0 스타일: inline (전문 포함)
    inline_md = generate_claude_md(
        "test-project", ["src", "tests"], preset,
        lazy_skills=False,
    )
    inline_tokens = measure_token_count(inline_md)

    # v1.1: lazy index (요약만)
    lazy_md = generate_claude_md(
        "test-project", ["src", "tests"], preset,
        lazy_skills=True,
    )
    lazy_tokens = measure_token_count(lazy_md)

    reduction = 1 - (lazy_tokens / max(inline_tokens, 1))
    print(f"Inline: {inline_tokens} tokens, Lazy: {lazy_tokens} tokens, Reduction: {reduction:.1%}")
    assert reduction >= 0.30, f"Expected ≥30% reduction, got {reduction:.1%}"


def test_claude_md_under_27k():
    """CLAUDE.md가 27K 토큰 이하인지 검증 (v1.1 NFR3)"""
    preset = load_preset("python")
    md = generate_claude_md(
        "test-project", ["src", "tests", "docs", "scripts"], preset,
        lazy_skills=True,
    )
    tokens = measure_token_count(md)
    assert tokens <= 27000, f"CLAUDE.md {tokens} tokens exceeds 27K limit"


def test_compaction_rules_present():
    """Compaction Rules 섹션이 CLAUDE.md에 포함되는지 검증"""
    preset = load_preset("python")
    md = generate_claude_md(
        "test-project", ["src"], preset, lazy_skills=True,
    )
    assert "## Compaction Rules" in md
    assert "ALWAYS preserve" in md
