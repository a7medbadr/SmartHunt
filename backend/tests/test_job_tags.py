import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.job_tags.models import JobTag


@pytest_asyncio.fixture
async def test_job(db_session: AsyncSession):
    await db_session.execute(delete(JobTag))
    await db_session.execute(delete(Job))
    await db_session.commit()

    job = Job(
        title="Senior Linux Administrator",
        company="SmartHunt Test Co",
        location="Riyadh",
        description="Test job for job tags",
        requirements="Linux, RHEL",
        source="test",
        url="http://example.com/job/tags/1",
    )

    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    yield job.id

    await db_session.execute(delete(JobTag))
    await db_session.execute(delete(Job))
    await db_session.commit()


@pytest.mark.asyncio
async def test_add_job_tag(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/job-tags",
        json={
            "job_id": test_job,
            "tag": "Remote",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["job_id"] == test_job
    assert data["tag"] == "Remote"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_duplicate_job_tag(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/job-tags",
        json={
            "job_id": test_job,
            "tag": "Urgent",
        },
    )
    assert response.status_code == 201

    response = await client.post(
        "/api/v1/job-tags",
        json={
            "job_id": test_job,
            "tag": "urgent",
        },
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_job_tags(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/job-tags",
        json={
            "job_id": test_job,
            "tag": "Dream Job",
        },
    )
    assert response.status_code == 201

    response = await client.post(
        "/api/v1/job-tags",
        json={
            "job_id": test_job,
            "tag": "High Salary",
        },
    )
    assert response.status_code == 201

    response = await client.get(f"/api/v1/job-tags/{test_job}")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["tag"] == "Dream Job"
    assert data[1]["tag"] == "High Salary"


@pytest.mark.asyncio
async def test_delete_job_tag(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/job-tags",
        json={
            "job_id": test_job,
            "tag": "Visa Sponsor",
        },
    )

    assert response.status_code == 201

    tag_id = response.json()["id"]

    response = await client.delete(f"/api/v1/job-tags/{tag_id}")

    assert response.status_code == 204

    response = await client.get(f"/api/v1/job-tags/{test_job}")

    assert response.status_code == 200

    assert all(item["id"] != tag_id for item in response.json())


@pytest.mark.asyncio
async def test_invalid_tag_id(client: AsyncClient):
    response = await client.delete("/api/v1/job-tags/999999")

    assert response.status_code == 404
