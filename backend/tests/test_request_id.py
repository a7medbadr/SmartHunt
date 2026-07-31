from httpx import ASGITransport, AsyncClient

from smarthunt.main import app


async def test_request_id_header_generated():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-correlation-id" in response.headers


async def test_request_id_header_preserved():
    request_id = "test-correlation-id"

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/api/v1/health/live",
            headers={"X-Request-ID": request_id},
        )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == request_id
    assert response.headers["x-correlation-id"] == request_id
