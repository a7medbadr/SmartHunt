import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from tests.conftest import TestSessionLocal
from smarthunt.database.models.job import Job
from smarthunt.job_tags.models import JobTag


@pytest_asyncio.fixture
async def test_job():
    async with TestSessionLocal() as session:
        job = Job(
            title="Senior Linux Administrator",
            company="SmartHunt Test Co",
            location="Riyadh",
            description="Test job for job tags",
            requirements="Linux, RHEL",
            source="test",
            url="http://example.com/job/tags/1",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id

    yield job_id

    async with TestSessionLocal() as session:
        await session.execute(delete(JobTag).where(JobTag.job_id == job_id))
        await session.execute(delete(Job).where(Job.id == job_id))
        await session.commit()


@pytest.mark.asyncio
async def test_add_job_tag(client: AsyncClient, test_job: int) -> None:
    payload = {"job_id": test_job, "tag": "Remote"}
    response = await client.post("/api/v1/job-tags", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] == test_job
    assert data["tag"] == "Remote"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_duplicate_job_tag(client: AsyncClient, test_job: int) -> None:
    await client.post("/api/v1/job-tags", json={"job_id": test_job, "tag": "Urgent"})

    response = await client.post(
        "/api/v1/job-tags", json={"job_id": test_job, "tag": "urgent"}
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_job_tags(client: AsyncClient, test_job: int) -> None:
    await client.post("/api/v1/job-tags", json={"job_id": test_job, "tag": "Dream Job"})
    await client.post("/api/v1/job-tags", json={"job_id": test_job, "tag": "High Salary"})

    response = await client.get(f"/api/v1/job-tags/{test_job}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["tag"] == "Dream Job"
    assert data[1]["tag"] == "High Salary"


@pytest.mark.asyncio
async def test_delete_job_tag(client: AsyncClient, test_job: int) -> None:
    create_response = await client.post(
        "/api/v1/job-tags", json={"job_id": test_job, "tag": "Visa Sponsor"}
    )
    tag_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/job-tags/{tag_id}")
    assert delete_response.status_code == 204

    list_response = await client.get(f"/api/v1/job-tags/{test_job}")
    assert all(t["id"] != tag_id for t in list_response.json())


@pytest.mark.asyncio
async def test_invalid_tag_id(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/job-tags/999999")
    assert response.status_code == 404
