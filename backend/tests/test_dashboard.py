import pytest
from httpx import AsyncClient
from fastapi import status

from smarthunt.database.models.job import Job


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


@pytest.mark.asyncio
async def test_dashboard_statistics_reflects_real_data(client: AsyncClient, db_session):
    before = (await client.get("/api/v1/dashboard/statistics")).json()

    db_session.add(
        Job(
            title="Dashboard Stats Test Job",
            company="Acme",
            location="Remote",
            source="linkedin",
            url="https://example.com/jobs/dashboard-stats-test",
        )
    )
    await db_session.commit()

    after = (await client.get("/api/v1/dashboard/statistics")).json()

    assert after["jobs"] == before["jobs"] + 1
    assert after["providers"] > 0
