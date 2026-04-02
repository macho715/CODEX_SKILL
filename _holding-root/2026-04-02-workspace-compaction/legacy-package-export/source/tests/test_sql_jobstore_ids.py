"""Tests for query-based SQL job id allocation."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.sql_jobstore_ids import _next_job_id


def _ping() -> None:
    """No-op job function for APScheduler integration tests."""


@pytest.fixture
def sql_scheduler(tmp_path: Path):
    """Create a scheduler backed by a SQLAlchemyJobStore."""
    pytest.importorskip("apscheduler")
    pytest.importorskip("sqlalchemy")

    from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
    from apscheduler.schedulers.background import BackgroundScheduler

    db_path = tmp_path / "jobs.sqlite3"
    store = SQLAlchemyJobStore(url=f"sqlite:///{db_path}")
    scheduler = BackgroundScheduler(jobstores={"default": store})
    scheduler.start(paused=True)

    try:
        yield scheduler, store
    finally:
        scheduler.shutdown(wait=False)


def test_next_job_id_returns_first_suffix_for_empty_store(sql_scheduler) -> None:
    """An empty SQL store should start numbering at 1."""
    _, store = sql_scheduler

    assert _next_job_id(store) == "job-1"


def test_next_job_id_uses_max_numeric_suffix(sql_scheduler) -> None:
    """The next id should be max suffix + 1, not first missing gap."""
    scheduler, store = sql_scheduler
    scheduler.add_job(_ping, "interval", seconds=60, id="job-1")
    scheduler.add_job(_ping, "interval", seconds=60, id="job-3")

    assert _next_job_id(store) == "job-4"


def test_next_job_id_ignores_other_prefixes_and_non_numeric_ids(sql_scheduler) -> None:
    """Only ids matching the requested prefix and numeric suffix should count."""
    scheduler, store = sql_scheduler
    scheduler.add_job(_ping, "interval", seconds=60, id="report-1")
    scheduler.add_job(_ping, "interval", seconds=60, id="sync-final")
    scheduler.add_job(_ping, "interval", seconds=60, id="sync-7")

    assert _next_job_id(store, prefix="sync") == "sync-8"


def test_next_job_id_uses_sql_query_not_get_all_jobs(sql_scheduler, monkeypatch) -> None:
    """SQLAlchemyJobStore path should work even if get_all_jobs is unusable."""
    scheduler, store = sql_scheduler
    scheduler.add_job(_ping, "interval", seconds=60, id="queue-2")

    def _raise_on_get_all_jobs():
        raise AssertionError("query path should not call get_all_jobs()")

    monkeypatch.setattr(store, "get_all_jobs", _raise_on_get_all_jobs)

    assert _next_job_id(store, prefix="queue") == "queue-3"


def test_next_job_id_rejects_blank_prefix(sql_scheduler) -> None:
    """Blank prefixes should fail fast."""
    _, store = sql_scheduler

    with pytest.raises(ValueError, match="prefix"):
        _next_job_id(store, prefix="---")
