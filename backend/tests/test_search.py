import pytest
from unittest.mock import AsyncMock, MagicMock
from smarthunt.providers.manager import ProviderManager


class MockProvider:
    """Mock provider matching the expected interface for tests."""

    def __init__(self, name="mock_provider", jobs=None):
        self.name = name
        self.jobs = jobs or []

    async def search(self, query=None, location=None, **kwargs):
        return self.jobs


@pytest.mark.asyncio
async def test_search_jobs_endpoint(client, monkeypatch):
    # Mocking the provider search to prevent remote HTTP/Browser calls during testing
    mock_provider = MockProvider(jobs=[])
    mock_registry = MagicMock()
    mock_registry.providers = [mock_provider]

    # Patch the registry inside ProviderManager
    monkeypatch.setattr(
        "smarthunt.services.search_service.ProviderManager",
        lambda: ProviderManager(registry=mock_registry),
    )

    response = await client.get("/api/v1/search/jobs")
    print("\n[TEST DEBUG] Status Code:", response.status_code)
    print("[TEST DEBUG] Response Body:", response.text)
    
    assert response.status_code == 200
