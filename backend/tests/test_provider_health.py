import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.health.models import ProviderHealth


@pytest_asyncio.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    await db_session.execute(delete(ProviderHealth))
    await db_session.commit()

    yield

    await db_session.execute(delete(ProviderHealth))
    await db_session.commit()


@pytest.mark.asyncio
async def test_create_provider_health(client: AsyncClient):
    response = await client.post(
        "/api/v1/providers/health",
        json={
            "provider": "linkedin",
            "status": "UP",
            "response_time_ms": 320,
            "message": "OK",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "linkedin"
    assert data["status"] == "UP"


@pytest.mark.asyncio
async def test_list_provider_health(client: AsyncClient):
    await client.post(
        "/api/v1/providers/health",
        json={"provider": "linkedin", "status": "UP", "response_time_ms": 300, "message": "OK"},
    )
    await client.post(
        "/api/v1/providers/health",
        json={
            "provider": "indeed",
            "status": "DOWN",
            "response_time_ms": None,
            "message": "Timeout",
        },
    )

    response = await client.get("/api/v1/providers/health")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_single_provider_health(client: AsyncClient):
    await client.post(
        "/api/v1/providers/health",
        json={"provider": "linkedin", "status": "UP", "response_time_ms": 320, "message": "OK"},
    )

    response = await client.get("/api/v1/providers/health/linkedin")

    assert response.status_code == 200
    data = response.json()
    assert data["provider"] == "linkedin"
    assert data["status"] == "UP"
    assert data["response_time_ms"] == 320


@pytest.mark.asyncio
async def test_get_nonexistent_provider_health(client: AsyncClient):
    response = await client.get("/api/v1/providers/health/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_existing_provider_health(client: AsyncClient):
    await client.post(
        "/api/v1/providers/health",
        json={"provider": "linkedin", "status": "UP", "response_time_ms": 320, "message": "OK"},
    )

    response = await client.post(
        "/api/v1/providers/health",
        json={
            "provider": "linkedin",
            "status": "DOWN",
            "response_time_ms": None,
            "message": "Connection refused",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "DOWN"

    response = await client.get("/api/v1/providers/health/linkedin")
    detail = response.json()
    assert detail["status"] == "DOWN"
    assert detail["message"] == "Connection refused"

    response = await client.get("/api/v1/providers/health")
    assert len(response.json()) == 1
