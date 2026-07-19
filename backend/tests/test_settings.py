import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.settings.models import UserSettings


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    await db_session.execute(delete(UserSettings))
    await db_session.commit()

    yield

    await db_session.execute(delete(UserSettings))
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_settings(client: AsyncClient):
    response = await client.put(
        "/api/v1/settings",
        json={
            "theme": "dark",
            "language": "en",
            "email_notifications": True,
            "job_alerts": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"
    assert data["language"] == "en"
    assert data["email_notifications"] is True
    assert data["job_alerts"] is True


@pytest.mark.asyncio
async def test_update_settings(client: AsyncClient):
    await client.put(
        "/api/v1/settings",
        json={
            "theme": "dark",
            "language": "en",
            "email_notifications": True,
            "job_alerts": True,
        },
    )

    response = await client.put(
        "/api/v1/settings",
        json={
            "theme": "light",
            "language": "ar",
            "email_notifications": False,
            "job_alerts": False,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "light"
    assert data["language"] == "ar"
    assert data["email_notifications"] is False
    assert data["job_alerts"] is False

    response = await client.get("/api/v1/settings")
    assert response.json()["theme"] == "light"


@pytest.mark.asyncio
async def test_get_settings(client: AsyncClient):
    await client.put(
        "/api/v1/settings",
        json={
            "theme": "dark",
            "language": "en",
            "email_notifications": True,
            "job_alerts": True,
        },
    )

    response = await client.get("/api/v1/settings")

    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"
    assert data["language"] == "en"
