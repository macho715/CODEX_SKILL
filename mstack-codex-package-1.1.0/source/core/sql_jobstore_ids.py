"""Utilities for query-based job id allocation against SQL job stores.

This module is a prototype for the missing PR14 target described by the user.
It computes the next job id by querying persisted rows instead of relying on
in-memory counters.
"""

from __future__ import annotations

from collections.abc import Iterable
import re
from typing import Any


_BACKSLASH = "\\"


def _next_job_id(jobstore: Any, prefix: str = "job") -> str:
    """Return the next ``{prefix}-{n}`` id for a job store.

    For SQLAlchemy-backed APScheduler job stores, this function reads the
    persisted ``id`` column directly from the database table. For other job
    stores, it falls back to ``get_all_jobs()``.

    Args:
        jobstore: APScheduler job store or compatible object.
        prefix: Job id prefix. ``"job"`` becomes ids like ``job-1``.

    Returns:
        The next job id using the highest numeric suffix plus one.
    """
    normalized_prefix = _normalize_prefix(prefix)
    job_ids = (
        _load_ids_from_sql_jobstore(jobstore, normalized_prefix)
        if _supports_sql_query(jobstore)
        else _load_ids_from_generic_jobstore(jobstore)
    )
    next_number = _max_suffix(job_ids, normalized_prefix) + 1
    return f"{normalized_prefix}-{next_number}"


def _normalize_prefix(prefix: str) -> str:
    """Validate and normalize a job id prefix."""
    normalized = prefix.strip().rstrip("-")
    if not normalized:
        raise ValueError("prefix must contain at least one non-dash character")
    return normalized


def _supports_sql_query(jobstore: Any) -> bool:
    """Return True when the job store exposes SQLAlchemy table metadata."""
    jobs_t = getattr(jobstore, "jobs_t", None)
    engine = getattr(jobstore, "engine", None)
    return jobs_t is not None and engine is not None and hasattr(jobs_t, "c")


def _load_ids_from_sql_jobstore(jobstore: Any, prefix: str) -> list[str]:
    """Load matching ids directly from a SQLAlchemy job store table."""
    from sqlalchemy import select

    escaped_prefix = _escape_like(prefix)
    selectable = select(jobstore.jobs_t.c.id).where(
        jobstore.jobs_t.c.id.like(f"{escaped_prefix}-%", escape=_BACKSLASH)
    )
    with jobstore.engine.begin() as connection:
        return list(connection.execute(selectable).scalars())


def _load_ids_from_generic_jobstore(jobstore: Any) -> list[str]:
    """Load ids from a generic APScheduler-compatible job store."""
    if not hasattr(jobstore, "get_all_jobs"):
        raise TypeError("jobstore must provide SQL metadata or get_all_jobs()")

    return [
        job_id
        for job_id in (
            getattr(job, "id", None) for job in jobstore.get_all_jobs()
        )
        if isinstance(job_id, str)
    ]


def _max_suffix(job_ids: Iterable[str], prefix: str) -> int:
    """Return the highest numeric suffix for ``prefix`` across job ids."""
    max_value = 0
    prefix_marker = f"{prefix}-"
    for job_id in job_ids:
        if not job_id.startswith(prefix_marker):
            continue

        suffix = job_id[len(prefix_marker):]
        if re.fullmatch(r"\d+", suffix):
            max_value = max(max_value, int(suffix))

    return max_value


def _escape_like(value: str) -> str:
    """Escape a string for SQL ``LIKE`` with backslash escaping."""
    escaped = value.replace(_BACKSLASH, _BACKSLASH * 2)
    escaped = escaped.replace("%", _BACKSLASH + "%")
    escaped = escaped.replace("_", _BACKSLASH + "_")
    return escaped
