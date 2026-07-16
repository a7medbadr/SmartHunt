from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["health"])


@router.get("/live")
async def live():
    return {"status": "alive"}


@router.get("/ready")
async def ready():
    return {"status": "ready"}


@router.get("/info")
async def info():
    return {
        "status": "ok",
        "service": "smarthunt-backend",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
    }
