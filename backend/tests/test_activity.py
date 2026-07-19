import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.activity.models import Activity


@pytest_asyncio.fixture
async def clean_activities(db_session: AsyncSession):
    await db_session.execute(delete(Activity))
    await db_session.commit()

    yield

    await db_session.execute(delete(Activity))
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_and_list_activity(
    client: AsyncClient,
    clean_activities,
):
    response = await client.get("/api/v1/activity")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    payload = {
        "type": "application_created",
        "title": "Applied to Red Hat",
        "details": "Senior Linux Admin role",
    }

    response = await client.post("/api/v1/activity", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    created = response.json()

    response = await client.get("/api/v1/activity")
    assert response.status_code == status.HTTP_200_OK

    activities = response.json()

    assert len(activities) == 1
    assert activities[0]["id"] == created["id"]
    assert activities[0]["title"] == payload["title"]
