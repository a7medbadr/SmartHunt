from datetime import datetime, timedelta, timezone

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
        json={
            "title": "New Job",
            "message": "Linux Engineer posted",
            "type": "INFO",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "New Job"
    assert data["message"] == "Linux Engineer posted"
    assert data["type"] == "INFO"
    assert data["status"] == "SENT"
    assert data["channel"] == "IN_APP"
    assert data["priority"] == "NORMAL"
    assert data["read_at"] is None


@pytest.mark.asyncio
async def test_list_notifications(client: AsyncClient):
    for i in range(5):
        await client.post(
            "/api/v1/notifications",
            json={
                "title": f"Job {i}",
                "message": "msg",
                "type": "INFO",
            },
        )

    response = await client.get("/api/v1/notifications")

    assert response.status_code == 200
    assert len(response.json()) == 5


@pytest.mark.asyncio
async def test_pagination(client: AsyncClient):
    for i in range(25):
        await client.post(
            "/api/v1/notifications",
            json={
                "title": f"N{i}",
                "message": "msg",
                "type": "INFO",
            },
        )

    response = await client.get(
        "/api/v1/notifications?page=2&page_size=10"
    )

    assert response.status_code == 200
    assert len(response.json()) == 10


@pytest.mark.asyncio
async def test_mark_notification_read(client: AsyncClient):
    response = await client.post(
        "/api/v1/notifications",
        json={
            "title": "Read",
            "message": "msg",
            "type": "INFO",
        },
    )

    notification_id = response.json()["id"]

    response = await client.post(
        f"/api/v1/notifications/{notification_id}/read"
    )

    assert response.status_code == 200

    response = await client.get(
        "/api/v1/notifications"
    )

    assert response.json()[0]["status"] == "READ"
    assert response.json()[0]["read_at"] is not None


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient):
    for i in range(3):
        await client.post(
            "/api/v1/notifications",
            json={
                "title": f"Job{i}",
                "message": "msg",
                "type": "INFO",
            },
        )

    response = await client.post(
        "/api/v1/notifications/read-all"
    )

    assert response.status_code == 200
    assert response.json()["updated"] == 3

    response = await client.get(
        "/api/v1/notifications/unread-count"
    )

    assert response.json()["count"] == 0


@pytest.mark.asyncio
async def test_unread_count(client: AsyncClient):
    for i in range(4):
        await client.post(
            "/api/v1/notifications",
            json={
                "title": f"Job{i}",
                "message": "msg",
                "type": "INFO",
            },
        )

    response = await client.get(
        "/api/v1/notifications/unread-count"
    )

    assert response.status_code == 200
    assert response.json()["count"] == 4


@pytest.mark.asyncio
async def test_cleanup_expired_notifications(client: AsyncClient):
    await client.post(
        "/api/v1/notifications",
        json={
            "title": "Expired",
            "message": "msg",
            "type": "INFO",
            "expires_at": (
                datetime.now(timezone.utc) - timedelta(days=1)
            ).isoformat(),
        },
    )

    response = await client.post(
        "/api/v1/notifications/cleanup"
    )

    assert response.status_code == 200
    assert response.json()["deleted"] == 1

    response = await client.get(
        "/api/v1/notifications"
    )

    assert response.json() == []


@pytest.mark.asyncio
async def test_mark_read_nonexistent(client: AsyncClient):
    response = await client.post(
        "/api/v1/notifications/999999/read"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_notification(client: AsyncClient):
    response = await client.post(
        "/api/v1/notifications",
        json={
            "title": "Delete",
            "message": "msg",
            "type": "INFO",
        },
    )

    notification_id = response.json()["id"]

    response = await client.delete(
        f"/api/v1/notifications/{notification_id}"
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_nonexistent_notification(client: AsyncClient):
    response = await client.delete(
        "/api/v1/notifications/999999"
    )

    assert response.status_code == 404
