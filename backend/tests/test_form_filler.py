import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_fill_form(
    client: AsyncClient,
):

    response = await client.post(
        "/api/v1/browser/playwright/fill-form",
        json={
            "job_url": "https://example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "status" in data


@pytest.mark.asyncio
async def test_fill_form_invalid_payload(
    client: AsyncClient,
):

    response = await client.post(
        "/api/v1/browser/playwright/fill-form",
        json={},
    )

    assert response.status_code == 422
