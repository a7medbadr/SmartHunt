import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job import FailedSchedulerJob
from smarthunt.scheduler.history.models import SchedulerHistory
from smarthunt.scheduler.jobs import (
    TANQEEB_DAILY_PROVIDER,
    discover_linux,
    discover_tanqeeb_daily,
    linkedin_session_healthcheck,
    recycle_browser,
)

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


@pytest.mark.asyncio
async def test_discover_tanqeeb_daily_sweeps_every_topic_and_records_summary(
    monkeypatch, db_session: AsyncSession
):
    """discover_tanqeeb_daily should run one restricted discover() call
    per TOPIC_QUERIES entry (mocked here rather than hitting the real
    site 5x — Tanqeeb's own real-search behavior is already covered
    elsewhere) and write one summary scheduler_history row under
    TANQEEB_DAILY_PROVIDER for SchedulerService.catch_up_scheduled_jobs()
    to key off of."""
    calls = []

    async def fake_discover(self, *, query, location=None, provider="manual-run", providers=None):
        calls.append({"query": query, "providers": providers})
        return {"providers": 1, "discovered": 0, "inserted": 2, "duplicates": 0}

    monkeypatch.setattr(DiscoveryService, "discover", fake_discover)

    await discover_tanqeeb_daily()

    assert len(calls) == 5  # one per TOPIC_QUERIES entry
    assert all(c["providers"] == ["tanqeeb"] for c in calls)

    result = await db_session.execute(
        select(SchedulerHistory).where(SchedulerHistory.provider == TANQEEB_DAILY_PROVIDER)
    )
    history = result.scalars().first()
    assert history is not None
    assert history.status == "completed"
    assert history.jobs_found == 10  # 5 topics * 2 inserted each


@pytest.mark.asyncio
async def test_discover_tanqeeb_daily_continues_past_a_failing_topic(
    monkeypatch, db_session: AsyncSession
):
    call_count = 0

    async def fake_discover(self, *, query, location=None, provider="manual-run", providers=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("provider network error")
        return {"providers": 1, "discovered": 0, "inserted": 0, "duplicates": 0}

    monkeypatch.setattr(DiscoveryService, "discover", fake_discover)

    # Must not raise, and must still attempt the remaining topics.
    await discover_tanqeeb_daily()
    assert call_count == 5


"""recycle_browser regression tests: added 2026-08-06 after a live incident
traced a trivial Ollama request timing out to host CPU contention from a
long-lived Chromium renderer process, not an AI/timeout bug — every
browser-using provider already closes its own context correctly, but
Chromium's own idle renderer-process pool accumulates over many hours on
this resource-constrained host regardless. recycle_browser periodically
tears the shared browser down so it relaunches clean."""


@pytest.mark.asyncio
async def test_recycle_browser_is_noop_when_not_running(monkeypatch):
    from smarthunt.browser.playwright.manager import browser_manager

    monkeypatch.setattr(browser_manager, "browser", None)

    close_called = False

    async def _close(self):
        nonlocal close_called
        close_called = True

    monkeypatch.setattr(type(browser_manager), "close", _close)

    await recycle_browser()

    assert close_called is False


@pytest.mark.asyncio
async def test_recycle_browser_closes_when_running(monkeypatch):
    from smarthunt.browser.playwright.manager import browser_manager

    monkeypatch.setattr(browser_manager, "browser", object())

    close_called = False

    async def _close(self):
        nonlocal close_called
        close_called = True

    monkeypatch.setattr(type(browser_manager), "close", _close)

    await recycle_browser()

    assert close_called is True


"""linkedin_session_healthcheck regression tests: added 2026-08-06 per
explicit request for the project to keep its own LinkedIn session alive
between the periodic scans instead of letting it silently go stale."""


@pytest.mark.asyncio
async def test_linkedin_session_healthcheck_saves_state_on_success(monkeypatch):
    from smarthunt.browser.playwright.manager import browser_manager

    monkeypatch.setattr(browser_manager, "browser", object())

    async def _launch(self, *args, **kwargs):
        pass

    async def _get_page(self, provider):
        return object()

    save_state_called = False

    async def _save_state(self, provider):
        nonlocal save_state_called
        save_state_called = True

    monkeypatch.setattr(type(browser_manager), "launch", _launch)
    monkeypatch.setattr(type(browser_manager), "get_page", _get_page)
    monkeypatch.setattr(type(browser_manager), "save_state", _save_state)

    async def _login(page):
        return {"status": "SUCCESS"}

    monkeypatch.setattr("smarthunt.browser.providers.linkedin.login.linkedin_login", _login)

    await linkedin_session_healthcheck()

    assert save_state_called is True


@pytest.mark.asyncio
async def test_linkedin_session_healthcheck_notifies_owner_on_manual_required(
    monkeypatch, db_session: AsyncSession
):
    from smarthunt.browser.playwright.manager import browser_manager
    from smarthunt.notifications.models import Notification

    monkeypatch.setattr(browser_manager, "browser", object())

    async def _launch(self, *args, **kwargs):
        pass

    async def _get_page(self, provider):
        return object()

    monkeypatch.setattr(type(browser_manager), "launch", _launch)
    monkeypatch.setattr(type(browser_manager), "get_page", _get_page)

    async def _login(page):
        return {"status": "MANUAL_REQUIRED"}

    monkeypatch.setattr("smarthunt.browser.providers.linkedin.login.linkedin_login", _login)

    await linkedin_session_healthcheck()

    result = await db_session.execute(
        select(Notification).where(Notification.title == "لينكدان محتاج تدخل يدوي")
    )
    notification = result.scalars().first()
    assert notification is not None
    assert notification.priority == "HIGH"

    await db_session.execute(delete(Notification).where(Notification.id == notification.id))
    await db_session.commit()
