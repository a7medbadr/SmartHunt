import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.job_notes.models import JobNote


@pytest_asyncio.fixture
async def test_job(db_session: AsyncSession):
    await db_session.execute(delete(JobNote))
    await db_session.execute(delete(Job))
    await db_session.commit()

    job = Job(
        title="Senior Linux Administrator",
        company="SmartHunt Test Co",
        location="Riyadh",
        description="Test job for job notes",
        requirements="Linux, RHEL",
        source="test",
        url="http://example.com/job/1",
    )

    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    yield job.id

    await db_session.execute(delete(JobNote))
    await db_session.execute(delete(Job))
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_job_note(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/job-notes",
        json={"job_id": test_job, "note": "HR called me."},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["job_id"] == test_job
    assert data["note"] == "HR called me."


@pytest.mark.asyncio
async def test_list_job_notes(client: AsyncClient, test_job: int):
    await client.post(
        "/api/v1/job-notes",
        json={"job_id": test_job, "note": "Need RHCE before interview."},
    )

    await client.post(
        "/api/v1/job-notes",
        json={"job_id": test_job, "note": "Follow up next Monday."},
    )

    response = await client.get(f"/api/v1/job-notes/{test_job}")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


@pytest.mark.asyncio
async def test_update_job_note(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/job-notes",
        json={"job_id": test_job, "note": "Salary discussed."},
    )

    note_id = response.json()["id"]

    response = await client.patch(
        f"/api/v1/job-notes/{note_id}",
        json={"note": "Salary discussed - 20k SAR."},
    )

    assert response.status_code == 200
    assert response.json()["note"] == "Salary discussed - 20k SAR."


@pytest.mark.asyncio
async def test_delete_job_note(client: AsyncClient, test_job: int):
    response = await client.post(
        "/api/v1/job-notes",
        json={"job_id": test_job, "note": "To be deleted."},
    )

    note_id = response.json()["id"]

    response = await client.delete(f"/api/v1/job-notes/{note_id}")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_invalid_note_id(client: AsyncClient):
    response = await client.patch(
        "/api/v1/job-notes/999999",
        json={"note": "Doesn't matter."},
    )

    assert response.status_code == 404

    response = await client.delete("/api/v1/job-notes/999999")

    assert response.status_code == 404
