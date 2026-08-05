import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.database.models.job import Job


@pytest_asyncio.fixture
async def test_job(db_session: AsyncSession):
    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Job))
    await db_session.commit()

    job = Job(
        title="Senior Linux Administrator",
        company="SmartHunt Test Co",
        location="Riyadh",
        description="Test job for apply queue",
        requirements="Linux, RHEL",
        source="test",
        url="http://example.com/job/apply-queue/1",
    )

    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    yield job.id

    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Job))
    await db_session.commit()


@pytest.mark.asyncio
async def test_add_to_queue(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] == test_job
    assert data["provider"] == "linkedin"
    assert data["status"] == "PENDING"
    assert data["priority"] == 1


@pytest.mark.asyncio
async def test_list_queue(client: AsyncClient, test_job: int):
    await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )

    response = await client.get("/api/v1/apply-queue")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


@pytest.mark.asyncio
async def test_update_queue_status(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )
    item_id = response.json()["id"]

    response = await client.patch(f"/api/v1/apply-queue/{item_id}", json={"status": "RUNNING"})

    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"


@pytest.mark.asyncio
async def test_update_queue_status_invalid(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )
    item_id = response.json()["id"]

    response = await client.patch(f"/api/v1/apply-queue/{item_id}", json={"status": "BOGUS"})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_from_queue(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )
    item_id = response.json()["id"]

    response = await client.delete(f"/api/v1/apply-queue/{item_id}")
    assert response.status_code == 204

    response = await client.get("/api/v1/apply-queue")
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_nonexistent_queue_item(client: AsyncClient):
    response = await client.delete("/api/v1/apply-queue/999999")
    assert response.status_code == 404


@pytest.fixture(autouse=True)
def mock_playwright_apply(monkeypatch):
    """quick-apply drives the real playwright_engine.apply() through
    AutoApplyWorker.process_item() — mocked here for the same reason as
    test_auto_apply_worker.py: these tests are about the queue/Job
    plumbing (creating a Job from a bare URL, inferring provider,
    running the specific item just created), not the browser mechanics,
    which already have their own coverage in test_playwright_engine.py."""

    async def fake_apply(job_url, provider="linkedin", application_id=None, db=None, job_id=None):
        return {"status": "SUCCESS", "job_url": job_url}

    monkeypatch.setattr(
        "smarthunt.recruitment.auto_apply_worker.playwright_engine.apply",
        fake_apply,
    )


@pytest.mark.asyncio
async def test_quick_apply_creates_job_and_applies(client: AsyncClient, db_session: AsyncSession):
    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Job))
    await db_session.commit()

    response = await client.post(
        "/api/v1/apply-queue/quick-apply",
        json={
            "url": "https://www.linkedin.com/jobs/view/quick-apply-test",
            "title": "Storage Administrator",
            "company": "Acme Gulf",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["provider"] == "linkedin"

    result = await db_session.execute(
        select(Job).where(Job.url == "https://www.linkedin.com/jobs/view/quick-apply-test")
    )
    job = result.scalar_one()
    assert job.title == "Storage Administrator"
    assert job.company == "Acme Gulf"

    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Job))
    await db_session.commit()


@pytest.mark.asyncio
async def test_quick_apply_reuses_existing_job_for_same_url(
    client: AsyncClient, test_job: int, db_session: AsyncSession
):
    result = await db_session.execute(select(Job).where(Job.id == test_job))
    existing_job = result.scalar_one()

    response = await client.post(
        "/api/v1/apply-queue/quick-apply",
        json={
            "url": existing_job.url,
            "title": "Different title, should be ignored",
            "company": "Different company, should be ignored",
        },
    )

    assert response.status_code == 200
    assert response.json()["job_id"] == test_job

    count = await db_session.execute(select(Job).where(Job.url == existing_job.url))
    assert len(list(count.scalars().all())) == 1


@pytest.mark.asyncio
async def test_quick_apply_infers_provider_from_url(client: AsyncClient, db_session: AsyncSession):
    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Job))
    await db_session.commit()

    response = await client.post(
        "/api/v1/apply-queue/quick-apply",
        json={
            "url": "https://www.bayt.com/en/saudi-arabia/jobs/quick-apply-test",
            "title": "VMware Administrator",
            "company": "Acme Gulf",
        },
    )

    assert response.status_code == 200
    assert response.json()["provider"] == "bayt"

    await db_session.execute(delete(ApplyQueueItem))
    await db_session.execute(delete(Job))
    await db_session.commit()
