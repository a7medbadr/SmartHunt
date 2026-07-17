from fastapi import APIRouter

from smarthunt.providers.registry import ProviderRegistry
from smarthunt.providers.statistics import provider_stats

router = APIRouter()


@router.get("")
async def list_providers():
    registry = ProviderRegistry()
    return [p.name.lower() for p in registry.providers()]


@router.get("/statistics")
async def get_provider_statistics():
    return provider_stats.get_summary()
