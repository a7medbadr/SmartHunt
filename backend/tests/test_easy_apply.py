import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_easy_apply(client: AsyncClient):

    response = await client.post(
        "/api/v1/browser/playwright/easy-apply",
        json={"job_url": "https://www.linkedin.com/jobs/view/test"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "status" in data


@pytest.mark.asyncio
async def test_easy_apply_invalid_payload(client: AsyncClient):

    response = await client.post(
        "/api/v1/browser/playwright/easy-apply",
        json={},
    )

    assert response.status_code == 422
