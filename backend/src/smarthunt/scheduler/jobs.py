from smarthunt.services.discovery_service import DiscoveryService


async def discover_python():
    service = DiscoveryService()
    await service.discover(keyword="python")


async def discover_linux():
    service = DiscoveryService()
    await service.discover(keyword="linux")


async def discover_devops():
    service = DiscoveryService()
    await service.discover(keyword="devops")
