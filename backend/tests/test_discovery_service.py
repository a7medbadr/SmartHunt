import pytest

from smarthunt.services.discovery_service import DiscoveryService


@pytest.mark.asyncio
async def test_discovery_service_initialization():
    service = DiscoveryService(None)

    assert service.jobs is not None
    assert service.registry is not None
