import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_start_engine(client: AsyncClient):
    response = await client.post("/api/v1/browser/playwright/start")

    assert response.status_code == 200
    assert response.json() == {"status": "started", "provider": None, "job_url": None}


@pytest.mark.asyncio
async def test_stop_engine(client: AsyncClient):
    await client.post("/api/v1/browser/playwright/start")
    response = await client.post("/api/v1/browser/playwright/stop")

    assert response.status_code == 200
    assert response.json()["status"] == "stopped"


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/login", json={"provider": "linkedin"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["provider"] == "linkedin"


@pytest.mark.asyncio
async def test_apply(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["job_url"] == "https://example.com/job/1"


@pytest.mark.asyncio
async def test_screenshot(client: AsyncClient):
    response = await client.post("/api/v1/browser/playwright/screenshot")

    assert response.status_code == 200
    assert response.json() == {"path": "screenshots/test.png"}
