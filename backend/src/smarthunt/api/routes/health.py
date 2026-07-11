from datetime import UTC, datetime

from fastapi import APIRouter

from smarthunt.api.schemas.health import HealthResponse

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


@router.get("/live")
async def live():
    return {"status": "alive"}


@router.get("/ready")
async def ready():
    return {"status": "ready"}


@router.get(
    "/info",
    response_model=HealthResponse,
)
async def info():
    return HealthResponse(
        status="ok",
        service="SmartHunt",
        version="1.0.0",
        timestamp=datetime.now(UTC),
    )
