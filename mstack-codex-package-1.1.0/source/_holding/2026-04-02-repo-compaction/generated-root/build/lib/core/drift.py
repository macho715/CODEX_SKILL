"""core/drift.py — 파일 드리프트 탐지 + Agent Teams Smart Router"""
from __future__ import annotations
from pathlib import Path
import hashlib
from .types import DriftItem, RouterResult, RouterDecision

# ── Smart Router 임계값 ───────────────────────────────
SINGLE_THRESHOLD = 3       # 파일 < 3 → SINGLE
SUBAGENT_THRESHOLD = 5     # 파일 < 5 (독립) → SUBAGENT, ≥ 5 → AGENT_TEAMS
AGENT_TEAMS_COST_RATIO = 3.5


def compute_hash(path: Path) -> str:
    """파일의 SHA256 해시를 계산한다. (앞 12자리만 반환)"""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def check_drift(project_dir: Path,
                expected_files: dict[str, str]) -> list[DriftItem]:
    """CLAUDE.md, skills, hooks의 드리프트를 탐지한다.

    Args:
        project_dir: 프로젝트 루트
        expected_files: {상대경로: 예상_해시} 딕셔너리

    Returns:
        DriftItem 리스트
    """
    results = []
    for rel_path, expected_hash in expected_files.items():
        full_path = project_dir / rel_path
        if not full_path.exists():
            results.append(DriftItem(rel_path, expected_hash, None, "missing"))
        else:
            actual = compute_hash(full_path)
            status = "ok" if actual == expected_hash else "modified"
            results.append(DriftItem(rel_path, expected_hash, actual, status))
    return results


def smart_route(
    changed_files: list[str],
    has_api_contract: bool = False,
    has_cross_module_deps: bool = False,
    cost_sensitive: bool = True,
) -> RouterResult:
    """작업 특성 기반으로 Subagent vs Agent Teams를 권고한다.

    v1.1 의사결정 트리:
    1. changed_files < 3 → SINGLE
    2. changed_files < 5 AND NOT cross_module AND NOT api_contract → SUBAGENT
    3. has_api_contract OR cross_module → AGENT_TEAMS
    4. changed_files >= 5 → AGENT_TEAMS
    """
    n = len(changed_files)

    # Decision 1: 소규모
    if n < SINGLE_THRESHOLD:
        return RouterResult(
            decision=RouterDecision.SINGLE,
            reason=f"Only {n} files — single session sufficient",
            file_count=n,
            coordination_needed=False,
            estimated_cost_ratio=1.0,
        )

    # Decision 2: 중규모, 독립적
    if n < SUBAGENT_THRESHOLD and not has_cross_module_deps and not has_api_contract:
        return RouterResult(
            decision=RouterDecision.SUBAGENT,
            reason=f"{n} files, no cross-module deps — subagent delegates efficiently",
            file_count=n,
            coordination_needed=False,
            estimated_cost_ratio=1.5,
        )

    # Decision 3: API 계약 or 모듈간 의존성
    if has_api_contract or has_cross_module_deps:
        cost_note = f" (⚠ ~{AGENT_TEAMS_COST_RATIO}x tokens)" if cost_sensitive else ""
        return RouterResult(
            decision=RouterDecision.AGENT_TEAMS,
            reason=f"Cross-module coordination needed{cost_note}",
            file_count=n,
            coordination_needed=True,
            estimated_cost_ratio=AGENT_TEAMS_COST_RATIO,
        )

    # Decision 4: 대규모
    cost_note = f" (⚠ ~{AGENT_TEAMS_COST_RATIO}x tokens)" if cost_sensitive else ""
    return RouterResult(
        decision=RouterDecision.AGENT_TEAMS,
        reason=f"{n} files — Agent Teams recommended{cost_note}",
        file_count=n,
        coordination_needed=True,
        estimated_cost_ratio=AGENT_TEAMS_COST_RATIO,
    )


def detect_cross_module(changed_files: list[str]) -> bool:
    """변경 파일이 2개 이상 모듈에 걸쳐 있는지 판단한다."""
    modules = set()
    for f in changed_files:
        parts = Path(f).parts
        if len(parts) >= 2:
            modules.add(parts[0])  # 최상위 디렉토리
    return len(modules) >= 2


def detect_api_contract(changed_files: list[str]) -> bool:
    """API 계약 파일 (schema, types, interface)이 변경되었는지 판단한다."""
    api_keywords = {"schema", "types", "interface", "api", "contract", "proto", "openapi"}
    for f in changed_files:
        stem = Path(f).stem.lower()
        if any(kw in stem for kw in api_keywords):
            return True
    return False
