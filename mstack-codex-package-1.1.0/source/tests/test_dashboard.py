"""tests/test_dashboard.py — core/dashboard.py 단위 테스트"""
from unittest.mock import patch, MagicMock
import subprocess
import pytest
from pathlib import Path
from core.dashboard import generate_dashboard_html, save_and_open, check_threshold
from core.cost import parse_jsonl, aggregate
from core.types import DashboardData


@pytest.fixture
def empty_dashboard():
    return DashboardData(
        daily=[], by_model={}, by_session=[],
        total_cost=0.0, total_sessions=0, period="N/A"
    )


@pytest.fixture
def sample_dashboard(sample_cost_jsonl):
    entries = parse_jsonl(sample_cost_jsonl)
    return aggregate(entries)


def test_generate_html_contains_chartjs(sample_dashboard):
    """Chart.js CDN URL이 HTML에 포함되는지 확인"""
    html = generate_dashboard_html(sample_dashboard)
    assert "cdnjs.cloudflare.com" in html
    assert "chart.umd.min.js" in html


def test_generate_html_contains_title(sample_dashboard):
    """대시보드 타이틀 포함 확인"""
    html = generate_dashboard_html(sample_dashboard)
    assert "mstack Cost Dashboard" in html


def test_generate_html_embeds_session_count(sample_dashboard):
    """세션 수가 HTML에 임베드되는지 확인"""
    html = generate_dashboard_html(sample_dashboard)
    assert str(sample_dashboard.total_sessions) in html


def test_save_creates_file(tmp_path, sample_dashboard):
    """save_and_open이 파일을 생성하는지 확인"""
    html = generate_dashboard_html(sample_dashboard)
    out = tmp_path / "dashboard.html"
    result = save_and_open(html, out, no_open=True)
    assert result.exists()
    assert result.read_text(encoding="utf-8") == html


def test_check_threshold_returns_false(empty_dashboard):
    """비용이 임계값 미만이면 False 반환"""
    result = check_threshold(empty_dashboard, threshold_usd=100.0)
    assert result is False


def test_check_threshold_returns_true(sample_dashboard):
    """비용이 임계값 초과이면 True 반환 (gh CLI 없어도 graceful)"""
    result = check_threshold(sample_dashboard, threshold_usd=0.001)
    assert result is True


def test_generate_html_empty_data(empty_dashboard):
    """빈 데이터도 HTML 생성 가능한지 확인 (오류 없음)"""
    html = generate_dashboard_html(empty_dashboard)
    assert "<html" in html


# ── save_and_open 추가 커버리지 ──────────────────────────


def test_save_and_open_opens_browser(tmp_path, sample_dashboard):
    """no_open=False일 때 webbrowser.open이 호출되는지 확인."""
    html = generate_dashboard_html(sample_dashboard)
    out = tmp_path / "dash.html"
    with patch("core.dashboard.webbrowser.open") as mock_open:
        result = save_and_open(html, out, no_open=False)
        assert result.exists()
        mock_open.assert_called_once_with(str(out))


def test_save_and_open_browser_oserror(tmp_path, sample_dashboard, capsys):
    """webbrowser.open이 OSError를 발생시키면 경고 출력 후 계속."""
    html = generate_dashboard_html(sample_dashboard)
    out = tmp_path / "dash.html"
    with patch("core.dashboard.webbrowser.open", side_effect=OSError("no display")):
        result = save_and_open(html, out, no_open=False)
        assert result.exists()
        captured = capsys.readouterr()
        assert "Could not open browser" in captured.out


# ── check_threshold 추가 커버리지 ──────────────────────────


def test_check_threshold_gh_success(sample_dashboard, capsys):
    """gh CLI 성공 시 'GitHub Issue created' 메시지 출력."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    with patch("core.dashboard.subprocess.run", return_value=mock_result):
        result = check_threshold(sample_dashboard, threshold_usd=0.001)
        assert result is True
        captured = capsys.readouterr()
        assert "GitHub Issue created" in captured.out


def test_check_threshold_gh_failure(sample_dashboard, capsys):
    """gh CLI 실패 시 (returncode != 0) 경고 출력."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    with patch("core.dashboard.subprocess.run", return_value=mock_result):
        result = check_threshold(sample_dashboard, threshold_usd=0.001)
        assert result is True
        captured = capsys.readouterr()
        assert "gh CLI failed" in captured.out


def test_check_threshold_gh_not_found(sample_dashboard, capsys):
    """gh CLI가 설치되지 않았을 때 FileNotFoundError 처리."""
    with patch("core.dashboard.subprocess.run", side_effect=FileNotFoundError):
        result = check_threshold(sample_dashboard, threshold_usd=0.001)
        assert result is True
        captured = capsys.readouterr()
        assert "gh CLI not found" in captured.out


def test_check_threshold_gh_timeout(sample_dashboard, capsys):
    """gh CLI 타임아웃 시 TimeoutExpired 처리."""
    with patch(
        "core.dashboard.subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=10),
    ):
        result = check_threshold(sample_dashboard, threshold_usd=0.001)
        assert result is True
        captured = capsys.readouterr()
        assert "gh CLI timed out" in captured.out
