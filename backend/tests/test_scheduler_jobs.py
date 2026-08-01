import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job import FailedSchedulerJob
from smarthunt.scheduler.history.models import SchedulerHistory
from smarthunt.scheduler.jobs import discover_linux

"""Regression tests: the APScheduler-registered discover_* jobs called
`async with track_scheduler_execution("...")`, but that function took a
handler callable and returned a plain dict — it was never an async
context manager. Every automatic scheduled discovery run crashed with
`TypeError: 'coroutine' object does not support the asynchronous context
manager protocol` and silently did nothing (no jobs discovered, no history
recorded), for as long as that mismatch existed. These verify the jobs now
actually run the real discovery pipeline and track their own outcome."""


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(
        delete(SchedulerHistory).where(SchedulerHistory.provider.like("scheduler:%"))
    )
    await db_session.execute(
        delete(FailedSchedulerJob).where(FailedSchedulerJob.provider.like("scheduler:%"))
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_discover_linux_runs_without_crashing_and_records_history(
    db_session: AsyncSession,
):
    await discover_linux()

    result = await db_session.execute(
        select(SchedulerHistory).where(SchedulerHistory.provider == "scheduler:linux")
    )
    history = result.scalars().first()
    assert history is not None
    assert history.status == "completed"


@pytest.mark.asyncio
async def test_discover_linux_records_failure_on_error(monkeypatch, db_session: AsyncSession):
    async def _boom(self, *args, **kwargs):
        raise RuntimeError("provider network error")

    monkeypatch.setattr(DiscoveryService, "discover", _boom)

    with pytest.raises(RuntimeError):
        await discover_linux()

    result = await db_session.execute(
        select(FailedSchedulerJob).where(FailedSchedulerJob.provider == "scheduler:linux")
    )
    failed = result.scalars().first()
    assert failed is not None
    assert failed.job_reference == "linux"
    assert "provider network error" in failed.last_error
