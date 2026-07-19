import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.notifications.models import Notification


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    await db_session.execute(delete(Notification))
    await db_session.commit()

    yield

    await db_session.execute(delete(Notification))
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_notification(client: AsyncClient):
    response = await client.post(
        "/api/v1/notifications",
        json={"title": "New Job", "message": "Linux Engineer posted", "type": "job"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Job"
    assert data["message"] == "Linux Engineer posted"
    assert data["type"] == "job"
    assert data["is_read"] is False


@pytest.mark.asyncio
async def test_list_notifications(client: AsyncClient):
    await client.post(
        "/api/v1/notifications",
        json={"title": "Job 1", "message": "msg 1", "type": "job"},
    )
    await client.post(
        "/api/v1/notifications",
        json={"title": "Job 2", "message": "msg 2", "type": "job"},
    )

    response = await client.get("/api/v1/notifications")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_mark_notification_read(client: AsyncClient):
    response = await client.post(
        "/api/v1/notifications",
        json={"title": "New Job", "message": "msg", "type": "job"},
    )
    notification_id = response.json()["id"]

    response = await client.patch(f"/api/v1/notifications/{notification_id}/read")

    assert response.status_code == 200
    assert response.json() == {"status": "updated"}

    response = await client.get("/api/v1/notifications")
    assert response.json()[0]["is_read"] is True


@pytest.mark.asyncio
async def test_delete_notification(client: AsyncClient):
    response = await client.post(
        "/api/v1/notifications",
        json={"title": "To Delete", "message": "msg", "type": "job"},
    )
    notification_id = response.json()["id"]

    response = await client.delete(f"/api/v1/notifications/{notification_id}")
    assert response.status_code == 204

    response = await client.get("/api/v1/notifications")
    assert response.json() == []


@pytest.mark.asyncio
async def test_mark_read_nonexistent(client: AsyncClient):
    response = await client.patch("/api/v1/notifications/999999/read")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_notification(client: AsyncClient):
    response = await client.delete("/api/v1/notifications/999999")
    assert response.status_code == 404
