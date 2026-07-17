import pytest
from httpx import AsyncClient, ASGITransport
from smarthunt.main import app


@pytest.mark.asyncio
async def test_search_jobs_endpoint():
    """Test job search endpoint returns expected data structure."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/search/jobs")
        assert response.status_code == 200
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)
        assert len(data["jobs"]) > 0
