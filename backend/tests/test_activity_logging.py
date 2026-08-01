import pytest
import pytest_asyncio
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.favorites.models import FavoriteJob

"""Regression tests: GET /api/v1/activity was reachable and DB-backed,
but nothing anywhere in the app ever created an Activity row — it would
always have returned an empty list in real use. These verify each real
flow now actually logs one."""


async def _latest_activity_type(client) -> str:
    response = await client.get("/api/v1/activity")
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) > 0
    return activities[0]["type"]


@pytest.mark.asyncio
async def test_application_creation_logs_activity(client):
    response = await client.post(
        "/api/v1/applications",
        json={"job_title": "Activity Test Job", "company": "Acme", "status": "Applied"},
    )
    assert response.status_code == 201
    assert await _latest_activity_type(client) == "application_created"


@pytest.mark.asyncio
async def test_saved_search_creation_logs_activity(client):
    response = await client.post(
        "/api/v1/saved-searches",
        json={"name": "Activity Test Search", "keyword": "devops"},
    )
    assert response.status_code == 201
    assert await _latest_activity_type(client) == "saved_search_created"


@pytest.mark.asyncio
async def test_cover_letter_generation_logs_activity(client):
    response = await client.post(
        "/api/v1/cover-letter/generate",
        json={"resume": "Linux Docker", "job": "Linux Docker AWS"},
    )
    assert response.status_code == 200
    assert await _latest_activity_type(client) == "cover_letter_generated"


@pytest_asyncio.fixture
async def cleanup_job(db_session: AsyncSession):
    await db_session.execute(delete(FavoriteJob))
    await db_session.execute(delete(Job))
    await db_session.commit()

    job = Job(
        title="Activity Logging Test Job",
        company="Acme",
        location="Remote",
        source="test",
        url="http://example.com/activity-logging-test",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    yield job.id

    await db_session.execute(delete(FavoriteJob))
    await db_session.execute(delete(Job))
    await db_session.commit()


@pytest.mark.asyncio
async def test_favorite_added_logs_activity(client, cleanup_job):
    response = await client.post("/api/v1/favorites", json={"job_id": cleanup_job})
    assert response.status_code == 201
    assert await _latest_activity_type(client) == "favorite_added"
