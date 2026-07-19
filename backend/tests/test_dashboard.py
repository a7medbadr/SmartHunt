import pytest
from httpx import AsyncClient
from fastapi import status

@pytest.mark.asyncio
async def test_get_dashboard_statistics_empty_db(client: AsyncClient):
    response = await client.get("/api/v1/dashboard/statistics")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "jobs" in data
    assert "applications" in data
    assert "favorites" in data
    assert "saved_searches" in data
    assert "providers" in data
    assert isinstance(data["jobs"], int)
