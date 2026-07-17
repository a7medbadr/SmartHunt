from fastapi import APIRouter

from smarthunt.providers.health.monitor import monitor

router = APIRouter()


@router.get("/health")
async def provider_health():

    return monitor.status()
