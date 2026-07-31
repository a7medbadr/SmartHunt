import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from smarthunt.middleware.rate_limit import RateLimitMiddleware
from smarthunt.api.routes import api_router


@pytest.fixture
def rate_limit_app():
    app = FastAPI()

    app.add_middleware(
        RateLimitMiddleware,
        requests_limit=100,
        window_seconds=60,
    )

    app.include_router(
        api_router,
        prefix="/api/v1",
    )

    return app


@pytest.mark.asyncio
async def test_rate_limit_allows_request(rate_limit_app):
    async with AsyncClient(
        transport=ASGITransport(app=rate_limit_app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health/live")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_rate_limit_blocks_excessive_requests(rate_limit_app):
    async with AsyncClient(
        transport=ASGITransport(app=rate_limit_app),
        base_url="http://test",
    ) as client:
        for _ in range(100):
            response = await client.get("/api/v1/health/live")
            assert response.status_code == 200

        response = await client.get("/api/v1/health/live")

    assert response.status_code == 429
