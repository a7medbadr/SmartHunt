import pytest
from httpx import ASGITransport, AsyncClient

from smarthunt.main import app


@pytest.mark.asyncio
async def test_system_version():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/system/version")

    assert response.status_code == 200

    body = response.json()

    assert body["application"] == "SmartHunt"
    assert "version" in body
    assert "environment" in body
    assert "python" in body
    assert "build" in body
