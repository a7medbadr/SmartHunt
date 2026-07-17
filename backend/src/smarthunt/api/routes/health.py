from fastapi import APIRouter, status

router = APIRouter(tags=["health"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness():
    return {"status": "ok"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness():
    return {"status": "ok"}
