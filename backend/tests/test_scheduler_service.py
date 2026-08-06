import asyncio

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.core.config import settings
from smarthunt.scheduler.history.models import SchedulerHistory
from smarthunt.scheduler.scheduler import scheduler
from smarthunt.services.scheduler_service import (
    SchedulerService,
    _run_catchup_jobs_sequentially,
)

"""Regression tests: SchedulerService().start() was never called anywhere
in the application (no lifespan hook, no startup event) — the real
AsyncIOScheduler instance never actually started, so
GET /api/v1/health/details's "scheduler" field was always "down" and
none of the scheduled jobs (discover_python/linux/devops,
process_failed_scheduler_jobs) ever ran automatically, regardless of
how correct their own logic was. Also: `settings.scheduler_enabled`,
which start() checks before doing anything, didn't exist on Settings at
all — start() would have raised AttributeError the first time anything
called it.

Everything below runs as one test, start-to-shutdown, inside the same
`await`: AsyncIOScheduler.start()/.shutdown() both call
asyncio.get_running_loop()-dependent APIs, and pytest-asyncio gives each
test its own event loop — splitting start/shutdown across a test and a
separate fixture teardown, or across two different test functions,
leaves the scheduler shut down against a loop that's already closed by
the time cleanup runs. Same class of issue as the DB pool fix in
database/session.py."""


def test_scheduler_enabled_setting_exists():
    # Real value is env-dependent (SCHEDULER_ENABLED=false in .env.test,
    # deliberately, per the module docstring above); this only confirms
    # the field exists and start() won't crash on AttributeError.
    assert isinstance(settings.scheduler_enabled, bool)


@pytest.mark.asyncio
async def test_scheduler_service_start_and_shutdown():
    assert scheduler.running is False

    try:
        settings.scheduler_enabled = True
        SchedulerService().start()

        assert scheduler.running is True
        job_ids = {job.id for job in scheduler.get_jobs()}
        assert {
            "discover_linux",
            "discover_openshift",
            "discover_vmware",
            "discover_storage",
            "discover_devops",
            "process_failed_scheduler_jobs",
            "scan_linkedin_home_feed_hourly",
            "daily_morning_discovery",
            "scan_all_linkedin_accounts_daily",
            "scan_hashtags_daily",
        } <= job_ids

        settings.scheduler_enabled = False
        SchedulerService().start()
        # already running — start() is idempotent, disabling afterward
        # doesn't stop it (that's a separate, deliberate concern)
        assert scheduler.running is True
    finally:
        settings.scheduler_enabled = True
        if scheduler.running:
            scheduler.shutdown(wait=False)
        scheduler.remove_all_jobs()


@pytest.mark.asyncio
async def test_scheduler_service_start_is_noop_when_disabled():
    try:
        settings.scheduler_enabled = False
        SchedulerService().start()
        assert scheduler.running is False
    finally:
        settings.scheduler_enabled = True


"""_run_catchup_jobs_sequentially / catch_up_scheduled_jobs regression
tests: added 2026-08-06 after a real OpenShift crash loop — the previous
version fired every overdue job as its own concurrent asyncio.create_task,
so a restart with multiple jobs overdue at once (routine) ran several full
discovery passes (several driving real Chromium) fully concurrently
within seconds of boot, OOMKilling the pod (2Gi limit) and re-triggering
the same crash on every subsequent restart. These prove due jobs now run
one at a time, not concurrently."""


@pytest.mark.asyncio
async def test_run_catchup_jobs_sequentially_never_overlaps():
    currently_running = 0
    max_concurrent_seen = 0
    call_order = []

    async def make_job(name: str):
        async def job():
            nonlocal currently_running, max_concurrent_seen
            currently_running += 1
            max_concurrent_seen = max(max_concurrent_seen, currently_running)
            call_order.append(name)
            await asyncio.sleep(0.05)
            currently_running -= 1

        return job

    job_a = await make_job("a")
    job_b = await make_job("b")
    job_c = await make_job("c")

    await _run_catchup_jobs_sequentially([job_a, job_b, job_c])

    assert max_concurrent_seen == 1
    assert call_order == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_run_catchup_jobs_sequentially_continues_past_a_failing_job():
    call_order = []

    async def failing_job():
        call_order.append("failing")
        raise RuntimeError("provider crashed")

    async def healthy_job():
        call_order.append("healthy")

    # Must not raise, and must still attempt the remaining jobs.
    await _run_catchup_jobs_sequentially([failing_job, healthy_job])

    assert call_order == ["failing", "healthy"]


@pytest.mark.asyncio
async def test_catch_up_scheduled_jobs_runs_due_jobs_sequentially_not_concurrently(
    monkeypatch, db_session: AsyncSession
):
    """End-to-end: with no scheduler_history rows at all, every job is
    "due" (never run before) — the exact real-world shape of the crash
    (multiple jobs overdue on the same restart). Confirms
    catch_up_scheduled_jobs feeds them into the one sequential runner
    instead of spawning a separate concurrent task per job. Clears
    scheduler_history for the 8 catch-up-eligible providers first — other
    tests in this suite (test_scheduler_jobs.py etc.) commit real rows
    for these same providers via their own AsyncSessionLocal() sessions,
    which persist across tests same as this test's own writes would."""
    import smarthunt.services.scheduler_service as scheduler_service_module

    providers = [
        "scheduler:linux",
        "scheduler:openshift",
        "scheduler:vmware",
        "scheduler:storage",
        "scheduler:devops",
        "scheduler:linkedin-feed",
        "scheduler:linkedin-accounts",
        "scheduler:linkedin-hashtags",
    ]
    await db_session.execute(
        delete(SchedulerHistory).where(SchedulerHistory.provider.in_(providers))
    )
    await db_session.commit()

    sequential_calls = []

    async def fake_run_sequentially(due_jobs):
        sequential_calls.append(due_jobs)

    monkeypatch.setattr(
        scheduler_service_module, "_run_catchup_jobs_sequentially", fake_run_sequentially
    )
    monkeypatch.setattr(settings, "scheduler_enabled", True)

    await SchedulerService().catch_up_scheduled_jobs()
    await asyncio.sleep(0)  # let the created task actually run

    assert len(sequential_calls) == 1
    assert len(sequential_calls[0]) == 8  # all 8 catch-up-eligible jobs are due
