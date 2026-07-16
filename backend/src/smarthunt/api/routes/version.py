from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def version():
    return {
        "application": "SmartHunt",
        "version": "1.0.0",
        "api": "v1",
        "status": "stable"
    }
