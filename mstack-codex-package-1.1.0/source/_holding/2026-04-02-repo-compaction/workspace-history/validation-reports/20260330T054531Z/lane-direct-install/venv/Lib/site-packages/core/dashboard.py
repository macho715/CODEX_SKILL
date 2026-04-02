"""core/dashboard.py — Chart.js 기반 Interactive HTML 대시보드 생성"""
from __future__ import annotations
from pathlib import Path
import json
import webbrowser
import subprocess
from .types import DashboardData


def generate_dashboard_html(data: DashboardData) -> str:
    """Chart.js 대시보드 HTML을 생성한다.

    단일 HTML 파일 (CDN 의존). 필터: 기간, 모델.
    차트: Line(일별 비용), Pie(모델별), Table(세션별).
    """
    daily_json = json.dumps(data.daily)
    model_json = json.dumps(data.by_model)
    session_json = json.dumps(data.by_session)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="generated" content="{data.period}">
<title>mstack Cost Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.7/chart.umd.min.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:system-ui,-apple-system,sans-serif; background:#0d1117; color:#c9d1d9; padding:20px; }}
  h1 {{ color:#58a6ff; margin-bottom:8px; }}
  .summary {{ display:flex; gap:20px; margin:16px 0; }}
  .card {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; flex:1; }}
  .card .value {{ font-size:24px; font-weight:bold; color:#58a6ff; }}
  .card .label {{ font-size:12px; color:#8b949e; margin-top:4px; }}
  .charts {{ display:grid; grid-template-columns:2fr 1fr; gap:20px; margin:20px 0; }}
  .chart-box {{ background:#161b22; border:1px solid #30363d; border-radius:8px; padding:16px; }}
  table {{ width:100%; border-collapse:collapse; margin:20px 0; }}
  th,td {{ padding:8px 12px; text-align:left; border-bottom:1px solid #30363d; }}
  th {{ color:#58a6ff; font-size:12px; text-transform:uppercase; }}
  .warn {{ color:#f85149; font-weight:bold; }}
</style>
</head>
<body>
<h1>mstack Cost Dashboard</h1>
<p>Period: {data.period} | Sessions: {data.total_sessions}</p>

<div class="summary">
  <div class="card">
    <div class="value">${data.total_cost:.2f}</div>
    <div class="label">Total Cost (USD)</div>
  </div>
  <div class="card">
    <div class="value">{data.total_sessions}</div>
    <div class="label">Total Sessions</div>
  </div>
  <div class="card">
    <div class="value">${data.total_cost / max(data.total_sessions,1):.2f}</div>
    <div class="label">Avg Cost / Session</div>
  </div>
</div>

<div class="charts">
  <div class="chart-box">
    <h3>Daily Cost Trend</h3>
    <canvas id="dailyChart"></canvas>
  </div>
  <div class="chart-box">
    <h3>Cost by Model</h3>
    <canvas id="modelChart"></canvas>
  </div>
</div>

<h3>Session Details</h3>
<table>
  <thead><tr><th>Session</th><th>Model</th><th>Cost</th><th>Tokens</th><th>Duration</th></tr></thead>
  <tbody id="sessionTable"></tbody>
</table>

<script>
const daily = {daily_json};
const models = {model_json};
const sessions = {session_json};

// Daily Line Chart
new Chart(document.getElementById('dailyChart'), {{
  type: 'line',
  data: {{
    labels: daily.map(d => d.date),
    datasets: [{{
      label: 'Daily Cost ($)',
      data: daily.map(d => d.total_cost),
      borderColor: '#58a6ff',
      backgroundColor: 'rgba(88,166,255,0.1)',
      fill: true, tension: 0.3,
    }}]
  }},
  options: {{
    responsive: true,
    scales: {{ y: {{ beginAtZero: true, ticks: {{ color: '#8b949e' }} }}, x: {{ ticks: {{ color: '#8b949e' }} }} }},
    plugins: {{ legend: {{ labels: {{ color: '#c9d1d9' }} }} }}
  }}
}});

// Model Pie Chart
const modelLabels = Object.keys(models);
const modelColors = ['#58a6ff','#f0883e','#3fb950','#bc8cff','#f85149'];
new Chart(document.getElementById('modelChart'), {{
  type: 'doughnut',
  data: {{
    labels: modelLabels,
    datasets: [{{ data: Object.values(models), backgroundColor: modelColors }}]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#c9d1d9' }}, position: 'bottom' }} }}
  }}
}});

// Session Table
const tbody = document.getElementById('sessionTable');
sessions.forEach(s => {{
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${{s.session_id.slice(0,12)}}</td><td>${{s.model}}</td><td>${{s.cost.toFixed(4)}}</td><td>${{s.tokens.toLocaleString()}}</td><td>${{(s.duration/60).toFixed(1)}}m</td>`;
  tbody.appendChild(tr);
}});
</script>
</body>
</html>"""


def save_and_open(html: str, output_path: Path, no_open: bool = False) -> Path:
    """HTML을 파일로 저장하고 브라우저로 연다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    if not no_open:
        try:
            webbrowser.open(str(output_path))
        except OSError:
            print(f"[mstack] ⚠ Could not open browser. View: {output_path}")
    return output_path


def check_threshold(data: DashboardData, threshold_usd: float) -> bool:
    """비용 임계값 초과 여부를 확인하고, 초과 시 GitHub Issue 생성."""
    if data.total_cost <= threshold_usd:
        return False

    print(f"[mstack] ⚠ Cost ${data.total_cost:.2f} exceeds threshold ${threshold_usd:.2f}")

    # gh CLI로 Issue 생성 (없으면 graceful skip)
    try:
        title = f"[mstack] Cost alert: ${data.total_cost:.2f} (threshold: ${threshold_usd:.2f})"
        body = (
            f"## Cost Alert\n\n"
            f"- Period: {data.period}\n"
            f"- Total: ${data.total_cost:.2f}\n"
            f"- Threshold: ${threshold_usd:.2f}\n"
            f"- Sessions: {data.total_sessions}\n\n"
            f"### Model Breakdown\n"
        )
        for model, cost in data.by_model.items():
            body += f"- {model}: ${cost:.2f}\n"

        result = subprocess.run(
            ["gh", "issue", "create", "--title", title, "--body", body,
             "--label", "cost-alert"],
            capture_output=True, timeout=10
        )
        if result.returncode == 0:
            print("[mstack] ✅ GitHub Issue created")
        else:
            print(f"[mstack] ⚠ gh CLI failed (exit {result.returncode}). Skipping issue creation.")
    except FileNotFoundError:
        print("[mstack] ⚠ gh CLI not found. Skipping issue creation.")
    except subprocess.TimeoutExpired:
        print("[mstack] ⚠ gh CLI timed out. Skipping issue creation.")

    return True
