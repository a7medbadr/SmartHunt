import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy import delete

from smarthunt.activity.models import Activity
from smarthunt.database.session import AsyncSessionLocal


@pytest_asyncio.fixture
async def clean_activities():
    # Clean before test
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Activity))
        await session.commit()

    yield

    # Clean after test
    async with AsyncSessionLocal() as session:
        await session.execute(delete(Activity))
        await session.commit()


@pytest.mark.asyncio
async def test_create_and_list_activity(
    client: AsyncClient,
    clean_activities,
):
    # 1. Test empty list
    response = await client.get("/api/v1/activity")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    # 2. Create activity
    payload = {
        "type": "application_created",
        "title": "Applied to Red Hat",
        "details": "Senior Linux Admin role",
    }

    create_res = await client.post("/api/v1/activity", json=payload)
    assert create_res.status_code == status.HTTP_201_CREATED

    created_data = create_res.json()
    assert created_data["title"] == payload["title"]
    assert created_data["type"] == payload["type"]

    # 3. List activities and verify ordering
    list_res = await client.get("/api/v1/activity")
    assert list_res.status_code == status.HTTP_200_OK

    activities = list_res.json()
    assert len(activities) == 1
    assert activities[0]["id"] == created_data["id"]
