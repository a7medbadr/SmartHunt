import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.favorites.models import FavoriteJob


@pytest_asyncio.fixture
async def test_job(db_session: AsyncSession):
    await db_session.execute(delete(FavoriteJob))
    await db_session.execute(delete(Job))
    await db_session.commit()

    job = Job(
        title="Senior Linux Administrator",
        company="SmartHunt Test Co",
        location="Riyadh",
        description="Test job for favorites",
        requirements="Linux, RHEL",
        source="test",
        url="http://example.com/job/1",
    )

    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    yield job.id

    await db_session.execute(delete(FavoriteJob))
    await db_session.execute(delete(Job))
    await db_session.commit()


@pytest.mark.asyncio
async def test_add_favorite(client: AsyncClient, test_job: int):
    response = await client.post("/api/v1/favorites", json={"job_id": test_job})

    assert response.status_code == 201
    data = response.json()
    assert data["job_id"] == test_job
    assert "id" in data


@pytest.mark.asyncio
async def test_add_duplicate_favorite(client: AsyncClient, test_job: int):
    await client.post("/api/v1/favorites", json={"job_id": test_job})
    response = await client.post("/api/v1/favorites", json={"job_id": test_job})

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_list_favorites(client: AsyncClient, test_job: int):
    await client.post("/api/v1/favorites", json={"job_id": test_job})

    response = await client.get("/api/v1/favorites")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["job_id"] == test_job


@pytest.mark.asyncio
async def test_delete_favorite(client: AsyncClient, test_job: int):
    await client.post("/api/v1/favorites", json={"job_id": test_job})

    response = await client.delete(f"/api/v1/favorites/{test_job}")

    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}

    response = await client.get("/api/v1/favorites")
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_nonexistent_favorite(client: AsyncClient):
    response = await client.delete("/api/v1/favorites/999999")
    assert response.status_code == 404
