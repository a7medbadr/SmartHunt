from httpx import ASGITransport, AsyncClient

from smarthunt.main import app


async def test_rate_limit_allows_request():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200


async def test_rate_limit_blocks_excessive_requests():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        for _ in range(100):
            await client.get("/api/v1/health/live")

        response = await client.get("/api/v1/health/live")

    assert response.status_code == 429
