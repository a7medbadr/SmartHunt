import pytest
from httpx import ASGITransport, AsyncClient

from smarthunt.core.config import settings
from smarthunt.main import app


@pytest.mark.asyncio
async def test_health_live():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_details():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/details")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] in ("ok", "degraded")
    assert body["database"] in ("up", "down")
    assert body["scheduler"] in ("up", "down")
    assert body["playwright"] == "idle"
    assert body["version"] == settings.VERSION
