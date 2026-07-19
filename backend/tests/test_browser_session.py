import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.browser.session.models import BrowserSession


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    await db_session.execute(delete(BrowserSession))
    await db_session.commit()

    yield

    await db_session.execute(delete(BrowserSession))
    await db_session.commit()


@pytest.mark.asyncio
async def test_open_session(client: AsyncClient):
    response = await client.post("/api/v1/browser/session", json={"provider": "linkedin"})

    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "linkedin"
    assert data["status"] == "ACTIVE"
    assert data["closed_at"] is None


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient):
    await client.post("/api/v1/browser/session", json={"provider": "linkedin"})
    await client.post("/api/v1/browser/session", json={"provider": "indeed"})

    response = await client.get("/api/v1/browser/session")

    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_close_session(client: AsyncClient):
    response = await client.post("/api/v1/browser/session", json={"provider": "linkedin"})
    session_id = response.json()["id"]

    response = await client.patch(f"/api/v1/browser/session/{session_id}/close")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CLOSED"
    assert data["closed_at"] is not None


@pytest.mark.asyncio
async def test_close_nonexistent_session(client: AsyncClient):
    response = await client.patch("/api/v1/browser/session/999999/close")
    assert response.status_code == 404
