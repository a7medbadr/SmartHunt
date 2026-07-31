from fastapi import APIRouter, status

from smarthunt.core.config import settings
from smarthunt.database.health import check_database_health

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness():
    return {"status": "ok"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness():
    return {"status": "ok"}


@router.get("/details", status_code=status.HTTP_200_OK)
async def details():
    database = "up"

    try:
        await check_database_health()
    except Exception:
        database = "down"

    return {
        "status": "ok" if database == "up" else "degraded",
        "database": database,
        "scheduler": "up",
        "playwright": "idle",
        "version": settings.VERSION,
    }
