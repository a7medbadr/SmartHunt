import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_create_and_list_activity(client: AsyncClient):
    # 1. Test empty list
    response = await client.get("/api/v1/activity")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    # 2. Create activity
    payload = {
        "type": "application_created",
        "title": "Applied to Red Hat",
        "details": "Senior Linux Admin role"
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
