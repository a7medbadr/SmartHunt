import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.database.models.job import Job
from smarthunt.notifications.models import Notification


@pytest.fixture(autouse=True)
def mock_playwright_apply(monkeypatch):
    """AutoApplyWorker.process_next() now calls the real, composed
    playwright_engine.apply() (login -> open_job -> detect_form ->
    easy_apply) instead of a no-op stub. These tests are about the
    QUEUE's own orchestration (locking, status transitions, the
    job_id -> real Job.url lookup, the success notification) — the
    browser mechanics themselves already have dedicated coverage in
    test_playwright_engine.py, so apply() is mocked here rather than
    driving a real (or even fully Playwright-mocked) browser through
    every queue test."""

    calls = []

    async def fake_apply(job_url, provider="linkedin", application_id=None, db=None):
        calls.append({"job_url": job_url, "provider": provider})
        return {"status": "SUCCESS", "job_url": job_url}

    monkeypatch.setattr(
        "smarthunt.recruitment.auto_apply_worker.playwright_engine.apply",
        fake_apply,
    )

    return calls


@pytest_asyncio.fixture
async def test_job(db_session: AsyncSession):
    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Notification))
    await db_session.execute(delete(Job))
    await db_session.commit()

    job = Job(
        title="Senior Linux Administrator",
        company="SmartHunt Test Co",
        location="Riyadh",
        description="Test job for auto apply worker",
        requirements="Linux, RHEL",
        source="test",
        url="http://example.com/job/auto-apply/1",
    )

    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    yield job.id

    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Notification))
    await db_session.execute(delete(Job))
    await db_session.commit()


@pytest.mark.asyncio
async def test_process_next(client: AsyncClient, test_job: int):
    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )

    response = await client.post("/api/v1/apply-worker/next")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["job_id"] == test_job


@pytest.mark.asyncio
async def test_process_next_passes_the_real_job_url_and_provider(
    client: AsyncClient, test_job: int, mock_playwright_apply
):
    """Regression test: process_next() used to call
    playwright_engine.apply(job_url=f"job:{item.job_id}") — a literal
    placeholder string, never a real URL Playwright could navigate to.
    It must look up the queued Job and pass its actual url/provider."""

    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )

    await client.post("/api/v1/apply-worker/next")

    assert len(mock_playwright_apply) == 1
    assert mock_playwright_apply[0]["job_url"] == "http://example.com/job/auto-apply/1"
    assert mock_playwright_apply[0]["provider"] == "linkedin"


@pytest.mark.asyncio
async def test_process_next_fails_when_apply_fails(client: AsyncClient, test_job: int, monkeypatch):
    async def fake_apply(job_url, provider="linkedin", application_id=None, db=None):
        return {"status": "FAILED", "job_url": job_url, "reason": "no_application_form"}

    monkeypatch.setattr(
        "smarthunt.recruitment.auto_apply_worker.playwright_engine.apply",
        fake_apply,
    )

    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )

    response = await client.post("/api/v1/apply-worker/next")

    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_process_next_notifies_owner_on_success(
    client: AsyncClient, test_job: int, db_session: AsyncSession
):
    """Core product promise: applications happen unattended, then the
    owner is told afterward — a successful auto-apply must leave a
    Notification behind, not silently update a queue row."""

    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )

    await client.post("/api/v1/apply-worker/next")

    result = await db_session.execute(select(Notification))
    notifications = list(result.scalars().all())

    assert len(notifications) == 1
    assert "Senior Linux Administrator" in notifications[0].title
    assert notifications[0].channel == "TELEGRAM"


@pytest.mark.asyncio
async def test_process_next_does_not_notify_on_failure(
    client: AsyncClient, test_job: int, db_session: AsyncSession, monkeypatch
):
    async def fake_apply(job_url, provider="linkedin", application_id=None, db=None):
        return {"status": "FAILED", "job_url": job_url}

    monkeypatch.setattr(
        "smarthunt.recruitment.auto_apply_worker.playwright_engine.apply",
        fake_apply,
    )

    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )

    await client.post("/api/v1/apply-worker/next")

    result = await db_session.execute(select(Notification))
    assert list(result.scalars().all()) == []


@pytest.mark.asyncio
async def test_process_next_empty_queue(client: AsyncClient):
    response = await client.post("/api/v1/apply-worker/next")

    assert response.status_code == 200
    assert response.json() is None


@pytest.mark.asyncio
async def test_process_all(client: AsyncClient, test_job: int):
    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )
    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "indeed", "priority": 2},
    )

    response = await client.post("/api/v1/apply-worker/all")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["status"] == "SUCCESS" for item in data)


@pytest.mark.asyncio
async def test_retry_failed(client: AsyncClient, test_job: int, db_session: AsyncSession):
    response = await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )
    item_id = response.json()["id"]

    await db_session.execute(
        ApplyQueueItem.__table__.update()
        .where(ApplyQueueItem.id == item_id)
        .values(status="FAILED")
    )
    await db_session.commit()

    response = await client.post("/api/v1/apply-worker/retry")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == item_id
    assert data[0]["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_cancel(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )
    item_id = response.json()["id"]

    response = await client.post(f"/api/v1/apply-worker/cancel/{item_id}")

    assert response.status_code == 200
    assert response.json()["status"] == "FAILED"


@pytest.mark.asyncio
async def test_cancel_nonexistent(client: AsyncClient):
    response = await client.post("/api/v1/apply-worker/cancel/999999")
    assert response.status_code == 404
