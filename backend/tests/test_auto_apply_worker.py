import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
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
