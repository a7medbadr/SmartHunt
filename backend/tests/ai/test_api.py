import pytest


@pytest.mark.asyncio
async def test_ai_generate_endpoint(client):

    response = await client.post(
        "/api/v1/ai/generate",
        json={
            "prompt": "hello ai",
            "provider": "local",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["success"] is True
    assert body["provider"] == "local"
    assert "hello ai" in body["content"]


@pytest.mark.asyncio
async def test_ai_health_endpoint(client):

    response = await client.get(
        "/api/v1/ai/health",
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "healthy"
    assert "providers" in body
