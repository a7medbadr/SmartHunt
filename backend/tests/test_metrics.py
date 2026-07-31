import pytest
from httpx import ASGITransport, AsyncClient

from smarthunt.main import app


@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/metrics")

    assert response.status_code == 200

    body = response.text

    assert "# HELP" in body
    assert "# TYPE" in body
    assert "http_requests_total" in body
