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

    response = await client.patch(
        f"/api/v1/apply-queue/{item_id}", json={"status": "RUNNING"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RUNNING"


@pytest.mark.asyncio
async def test_update_queue_status_invalid(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/apply-queue",
        json={"job_id": test_job, "provider": "linkedin", "priority": 1},
    )
    item_id = response.json()["id"]

    response = await client.patch(
        f"/api/v1/apply-queue/{item_id}", json={"status": "BOGUS"}
    )

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
