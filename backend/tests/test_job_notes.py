import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from smarthunt.database.models.job import Job
from smarthunt.job_notes.models import JobNote
from conftest import TestSessionLocal


@pytest_asyncio.fixture
async def test_job():
    async with TestSessionLocal() as session:
        job = Job(
            title="Senior Linux Administrator",
            company="SmartHunt Test Co",
            location="Riyadh",
            description="Test job for job notes",
            requirements="Linux, RHEL",
            source="test",
            url="http://example.com/job/1",
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        job_id = job.id

    yield job_id

    async with TestSessionLocal() as session:
        await session.execute(delete(JobNote).where(JobNote.job_id == job_id))
        await session.execute(delete(Job).where(Job.id == job_id))
        await session.commit()


@pytest.mark.asyncio
async def test_create_job_note(client: AsyncClient, test_job: int) -> None:
    payload = {"job_id": test_job, "note": "HR called me."}
    response = await client.post("/api/v1/job-notes", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] == test_job
    assert data["note"] == "HR called me."
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_list_job_notes(client: AsyncClient, test_job: int) -> None:
    await client.post("/api/v1/job-notes", json={"job_id": test_job, "note": "Need RHCE before interview."})
    await client.post("/api/v1/job-notes", json={"job_id": test_job, "note": "Follow up next Monday."})

    response = await client.get(f"/api/v1/job-notes/{test_job}")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["note"] == "Need RHCE before interview."
    assert data[1]["note"] == "Follow up next Monday."


@pytest.mark.asyncio
async def test_update_job_note(client: AsyncClient, test_job: int) -> None:
    create_response = await client.post(
        "/api/v1/job-notes", json={"job_id": test_job, "note": "Salary discussed."}
    )
    note_id = create_response.json()["id"]

    response = await client.patch(
        f"/api/v1/job-notes/{note_id}", json={"note": "Salary discussed - 20k SAR."}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["note"] == "Salary discussed - 20k SAR."


@pytest.mark.asyncio
async def test_delete_job_note(client: AsyncClient, test_job: int) -> None:
    create_response = await client.post(
        "/api/v1/job-notes", json={"job_id": test_job, "note": "To be deleted."}
    )
    note_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/job-notes/{note_id}")
    assert delete_response.status_code == 204

    list_response = await client.get(f"/api/v1/job-notes/{test_job}")
    assert all(n["id"] != note_id for n in list_response.json())


@pytest.mark.asyncio
async def test_invalid_note_id(client: AsyncClient) -> None:
    response = await client.patch("/api/v1/job-notes/999999", json={"note": "Doesn't matter."})
    assert response.status_code == 404

    response = await client.delete("/api/v1/job-notes/999999")
    assert response.status_code == 404
