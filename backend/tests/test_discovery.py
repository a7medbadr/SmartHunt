import pytest


@pytest.mark.asyncio
async def test_discovery_run_does_not_crash(client):
    """Regression test: several providers didn't accept the page/limit
    kwargs ProviderRegistry.fetch_all_jobs always passes, and three more
    returned a dict instead of a list of jobs — both crashed the endpoint
    with an unhandled 500 instead of gracefully degrading per provider."""
    response = await client.post(
        "/api/v1/discovery/run",
        params={"query": "engineer", "location": "remote"},
    )

    assert response.status_code == 200

    data = response.json()
    assert data["providers"] == 12
    assert data["discovered"] >= 0
    assert data["inserted"] >= 0


@pytest.mark.asyncio
async def test_discovery_run_records_scheduler_history(client):
    before = await client.get("/api/v1/scheduler/history")
    before_count = len(before.json())

    response = await client.post(
        "/api/v1/discovery/run",
        params={"query": "engineer"},
    )
    assert response.status_code == 200

    after = await client.get("/api/v1/scheduler/history")
    after_count = len(after.json())

    assert after_count == before_count + 1
    assert after.json()[0]["provider"] == "manual-run"
