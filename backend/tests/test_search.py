import pytest

from smarthunt.database.models.job import Job


@pytest.mark.asyncio
async def test_search_jobs_endpoint(client, db_session):
    """Job search hits the real database, not a hardcoded fixture list."""
    db_session.add(
        Job(
            title="Senior Backend Engineer",
            company="Acme",
            location="Remote",
            source="linkedin",
            url="https://example.com/jobs/senior-backend-engineer",
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/search/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert isinstance(data["jobs"], list)
    assert len(data["jobs"]) > 0
    assert any(job["title"] == "Senior Backend Engineer" for job in data["jobs"])
