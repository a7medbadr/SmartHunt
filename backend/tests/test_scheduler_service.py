import pytest

from smarthunt.core.config import settings
from smarthunt.scheduler.scheduler import scheduler
from smarthunt.services.scheduler_service import SchedulerService

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
            "process_failed_scheduler_jobs",
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
