import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.history.models import SchedulerHistory


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    await db_session.execute(delete(SchedulerHistory))
    await db_session.commit()

    yield

    await db_session.execute(delete(SchedulerHistory))
    await db_session.commit()


@pytest.mark.asyncio
async def test_insert_scheduler_history(client: AsyncClient):
    response = await client.post(
        "/api/v1/scheduler/history",
        json={
            "provider": "linkedin",
            "status": "SUCCESS",
            "jobs_found": 41,
            "message": "Finished",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "linkedin"
    assert data["status"] == "SUCCESS"
    assert data["jobs_found"] == 41


@pytest.mark.asyncio
async def test_list_scheduler_history(client: AsyncClient):
    await client.post(
        "/api/v1/scheduler/history",
        json={"provider": "linkedin", "status": "SUCCESS", "jobs_found": 41, "message": "Finished"},
    )
    await client.post(
        "/api/v1/scheduler/history",
        json={"provider": "indeed", "status": "FAILED", "jobs_found": 0, "message": "Timeout"},
    )

    response = await client.get("/api/v1/scheduler/history")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_latest_scheduler_history(client: AsyncClient):
    await client.post(
        "/api/v1/scheduler/history",
        json={"provider": "linkedin", "status": "SUCCESS", "jobs_found": 10, "message": "First"},
    )
    await client.post(
        "/api/v1/scheduler/history",
        json={"provider": "indeed", "status": "SUCCESS", "jobs_found": 20, "message": "Second"},
    )

    response = await client.get("/api/v1/scheduler/history/latest")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "indeed"
    assert data["message"] == "Second"


@pytest.mark.asyncio
async def test_latest_scheduler_history_empty(client: AsyncClient):
    response = await client.get("/api/v1/scheduler/history/latest")
    assert response.status_code == 200
    assert response.json() is None
