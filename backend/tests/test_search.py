import pytest

@pytest.mark.asyncio
async def test_search_jobs_endpoint(client):
    response = await client.get("/api/v1/search/jobs")
    print("\n[TEST DEBUG] Status Code:", response.status_code)
    print("[TEST DEBUG] Response Body:", response.text)
    assert response.status_code == 200
