#!/usr/bin/env python3
"""세션별 비용 기록/조회. ccat cost 로도 접근 가능."""

import argparse
import json
from datetime import datetime
from pathlib import Path

LOG = Path.home() / ".claude" / "cost-logs" / "sessions.jsonl"

from types import MappingProxyType
_P = {"opus": (5, 25), "sonnet": (3, 15), "haiku": (1, 5)}  # $/MTok (in, out)
P = MappingProxyType(_P)  # 외부 변이 방지 (read-only view)

# ── 3-Tier 기본 비율 ─────────────────────────────────
DEFAULT_OPUS_RATIO = 0.25    # Lead 25%
DEFAULT_SONNET_RATIO = 0.75  # Workers 75%
IO_SPLIT_RATIO = 0.5         # input/output 반반 가정


def _c(ti, to, m="opus"):
    i, o = P[m]
    return round(ti / 1e6 * i + to / 1e6 * o, 2)


def calculate_3tier_cost(members, tokens, tier_split=None):
    """
    3-Tier 구성별 세션당 비용 계산.

    Args:
        members (int): 팀원 수 (1 이상)
        tokens (int): 총 토큰 수 (input + output)
        tier_split (dict, optional): {'opus': 0.25, 'sonnet': 0.75} 비율
                                     기본값은 Opus 25%, Sonnet 75%

    Returns:
        dict: {
            'total_cost': 총 비용,
            'opus_cost': Opus 비용,
            'sonnet_cost': Sonnet 비용,
            'cost_per_member': 1인당 비용
        }

    Raises:
        ValueError: members <= 0 또는 tokens < 0
    """
    if members <= 0:
        raise ValueError("members must be > 0")
    if tokens < 0:
        raise ValueError("tokens must be >= 0")

    if tier_split is None:
        tier_split = {'opus': DEFAULT_OPUS_RATIO, 'sonnet': DEFAULT_SONNET_RATIO}

    # 입출력 토큰 반반 가정
    ti = int(tokens * IO_SPLIT_RATIO)
    to = int(tokens * IO_SPLIT_RATIO)

    opus_tokens_in = int(ti * tier_split['opus'])
    opus_tokens_out = int(to * tier_split['opus'])
    sonnet_tokens_in = int(ti * tier_split['sonnet'])
    sonnet_tokens_out = int(to * tier_split['sonnet'])

    opus_cost = _c(opus_tokens_in, opus_tokens_out, "opus")
    sonnet_cost = _c(sonnet_tokens_in, sonnet_tokens_out, "sonnet")
    total_cost = opus_cost + sonnet_cost

    return {
        'total_cost': round(total_cost, 2),
        'opus_cost': opus_cost,
        'sonnet_cost': sonnet_cost,
        'cost_per_member': round(total_cost / members, 2)
    }


def log_start(team: str, members: int, mix: bool) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    e = {"ev": "start", "team": team, "ts": datetime.now().isoformat(),
         "n": members, "mix": mix}
    with open(LOG, "a") as f:
        f.write(json.dumps(e) + "\n")
    mode = "Opus+Sonnet" if mix else "All Opus"
    print(f"  [{team}] start | {members}명 ({mode})")


def log_end(team: str, ti: int, to: int) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    cost = _c(int(ti * DEFAULT_OPUS_RATIO), int(to * DEFAULT_OPUS_RATIO), "opus") + \
           _c(int(ti * DEFAULT_SONNET_RATIO), int(to * DEFAULT_SONNET_RATIO), "sonnet")
    e = {"ev": "end", "team": team, "ts": datetime.now().isoformat(),
         "ti": ti, "to": to, "cost": cost}
    with open(LOG, "a") as f:
        f.write(json.dumps(e) + "\n")
    print(f"  [{team}] end | {ti+to:,} tok | ${cost:.2f}")


def log_auto_end(session_id: str, timestamp: str | None = None) -> None:
    """Stop Hook에서 호출 — 세션 종료 자동 기록.

    토큰 데이터 없이도 동작한다 (타임스탬프만으로 세션 경계 추적).

    Args:
        session_id: 세션 식별자
        timestamp: ISO 형식 문자열 (None이면 현재 시각)
    """
    LOG.parent.mkdir(parents=True, exist_ok=True)
    ts = timestamp or datetime.now().isoformat()
    e = {"ev": "auto_end", "session_id": session_id, "ts": ts}
    with open(LOG, "a") as f:
        f.write(json.dumps(e) + "\n")
    print(f"  [auto] session {session_id} ended at {ts[:16]}")


def report(month: str | None = None) -> None:
    if not LOG.exists():
        print("기록 없음."); return
    total = 0.0
    for line in LOG.read_text().strip().split("\n"):
        if not line:
            continue
        try:
            s = json.loads(line)
        except json.JSONDecodeError:
            print(f"  ⚠ 손상된 라인 무시: {line[:60]}")
            continue
        if month and not s.get("ts", "").startswith(month):
            continue
        if s.get("ev") == "end":
            total += s.get("cost", 0)
            print(f"  {s.get('team', '?'):<20} ${s.get('cost', 0):<8.2f} {s.get('ts', '')[:16]}")
    print(f"  {'─'*40}\n  총: ${total:.2f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("start")
    s.add_argument("--team", required=True)
    s.add_argument("-n", type=int, default=3)
    s.add_argument("--mix", action="store_true")

    s = sub.add_parser("end")
    s.add_argument("--team", required=True)
    s.add_argument("--ti", type=int, required=True)
    s.add_argument("--to", type=int, required=True)

    s = sub.add_parser("report")
    s.add_argument("--month", default=None)

    s = sub.add_parser("auto-end")
    s.add_argument("--session-id", required=True)
    s.add_argument("--ts", default=None)

    a = p.parse_args()
    if a.cmd == "start":
        log_start(a.team, a.n, a.mix)
    elif a.cmd == "end":
        log_end(a.team, a.ti, a.to)
    elif a.cmd == "auto-end":
        log_auto_end(a.session_id, a.ts)
    elif a.cmd == "report":
        report(a.month)
    else:
        p.print_help()
