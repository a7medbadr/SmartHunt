from datetime import datetime, timezone

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job import FailedSchedulerJob
from smarthunt.scheduler.failed_job_service import FailedSchedulerJobService
from smarthunt.scheduler.retry_worker import scheduler_retry_worker

"""Regression tests: scheduler_retry_worker.process() used to only call
prepare_retry() (flip status to RETRY_PENDING/FAILED_FINAL) and never
actually re-ran anything — failed scheduler jobs would sit in
RETRY_PENDING forever with no dispatcher ever consuming that state. The
only existing test asserted `scheduler_retry_worker is not None`. These
verify the full retry loop: re-run, resolve on success, reset to FAILED
(not stuck at RUNNING) on repeat failure, and stop retrying once
MAX_RETRIES is exhausted or the job type is unrecognized."""


async def _make_failed_job(db: AsyncSession, **overrides) -> FailedSchedulerJob:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    job = FailedSchedulerJob(
        provider=overrides.get("provider", "scheduler:linux"),
        job_reference=overrides.get("job_reference", "linux"),
        status=overrides.get("status", "FAILED"),
        retry_count=overrides.get("retry_count", 0),
        last_error=overrides.get("last_error", "original failure"),
        created_at=now,
        updated_at=now,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(FailedSchedulerJob))
    await db_session.commit()


@pytest.mark.asyncio
async def test_retry_worker_resolves_job_on_successful_retry(monkeypatch, db_session: AsyncSession):
    async def _succeed(self, *, query, provider, **kwargs):
        return {"providers": 11, "discovered": 0, "inserted": 0, "duplicates": 0}

    monkeypatch.setattr(DiscoveryService, "discover", _succeed)

    job = await _make_failed_job(db_session)

    processed = await scheduler_retry_worker.process(db_session)
    await db_session.commit()

    assert len(processed) == 1
    assert processed[0].id == job.id
    assert processed[0].status == "SUCCESS"
    assert processed[0].retry_count == 1


@pytest.mark.asyncio
async def test_retry_worker_resets_to_failed_when_retry_fails_again(
    monkeypatch, db_session: AsyncSession
):
    async def _fail(self, *, query, provider, **kwargs):
        raise RuntimeError("still down")

    monkeypatch.setattr(DiscoveryService, "discover", _fail)

    job = await _make_failed_job(db_session, last_error="original failure")

    processed = await scheduler_retry_worker.process(db_session)
    await db_session.commit()

    assert processed[0].id == job.id
    assert processed[0].status == "FAILED"
    assert processed[0].retry_count == 1
    assert "still down" in processed[0].last_error


@pytest.mark.asyncio
async def test_retry_worker_marks_final_once_retries_exhausted(
    monkeypatch, db_session: AsyncSession
):
    call_count = 0

    async def _should_not_be_called(self, *, query, provider, **kwargs):
        nonlocal call_count
        call_count += 1
        return {"providers": 11, "discovered": 0, "inserted": 0, "duplicates": 0}

    monkeypatch.setattr(DiscoveryService, "discover", _should_not_be_called)

    job = await _make_failed_job(db_session, retry_count=FailedSchedulerJobService.MAX_RETRIES)

    processed = await scheduler_retry_worker.process(db_session)
    await db_session.commit()

    assert processed[0].id == job.id
    assert processed[0].status == "FAILED_FINAL"
    assert call_count == 0


@pytest.mark.asyncio
async def test_retry_worker_marks_final_for_unknown_job_reference(
    monkeypatch, db_session: AsyncSession
):
    call_count = 0

    async def _should_not_be_called(self, *, query, provider, **kwargs):
        nonlocal call_count
        call_count += 1

    monkeypatch.setattr(DiscoveryService, "discover", _should_not_be_called)

    job = await _make_failed_job(db_session, job_reference="some-unmapped-topic")

    processed = await scheduler_retry_worker.process(db_session)
    await db_session.commit()

    assert processed[0].id == job.id
    assert processed[0].status == "FAILED_FINAL"
    assert call_count == 0
