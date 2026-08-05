import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.discovery.service import DiscoveryService
from smarthunt.providers.settings.models import ProviderSetting

"""Regression coverage for the providers enable/disable feature: a
disabled provider must actually be excluded from discovery, not just
show as disabled in the UI."""


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(ProviderSetting))
    await db_session.commit()


@pytest.mark.asyncio
async def test_list_providers_defaults_to_enabled(client):
    response = await client.get("/api/v1/providers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 13
    assert all(p["enabled"] for p in data)
    linkedin = next(p for p in data if p["name"] == "linkedin")
    assert linkedin["real_discovery"] is True
    bayt = next(p for p in data if p["name"] == "bayt")
    assert bayt["real_discovery"] is False


@pytest.mark.asyncio
async def test_disable_and_reenable_provider(client):
    response = await client.patch("/api/v1/providers/linkedin", json={"enabled": False})
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    list_response = await client.get("/api/v1/providers")
    linkedin = next(p for p in list_response.json() if p["name"] == "linkedin")
    assert linkedin["enabled"] is False

    response = await client.patch("/api/v1/providers/linkedin", json={"enabled": True})
    assert response.status_code == 200
    assert response.json()["enabled"] is True


@pytest.mark.asyncio
async def test_update_unknown_provider_404(client):
    response = await client.patch("/api/v1/providers/not-a-real-site", json={"enabled": False})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_disabled_provider_excluded_from_discovery(client, db_session, monkeypatch):
    """The actual point of the feature: disabling a provider must stop it
    from being queried, not just look disabled in a list."""
    called_with = []

    async def fake_fetch_all_jobs(
        self, query=None, location=None, page=1, limit=25, providers=None
    ):
        called_with.extend(p.name for p in providers)
        return []

    monkeypatch.setattr(
        "smarthunt.providers.registry.ProviderRegistry.fetch_all_jobs", fake_fetch_all_jobs
    )

    disable_response = await client.patch("/api/v1/providers/bayt", json={"enabled": False})
    assert disable_response.status_code == 200

    await DiscoveryService(db_session).discover(query="python")

    assert "bayt" not in called_with
    assert "linkedin" in called_with
