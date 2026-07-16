from fastapi import APIRouter

router = APIRouter()

@router.get("")
async def version():
    return {
        "name": "SmartHunt",
        "version": "1.0.0",
        "git": "latest",
        "environment": "sandbox",
        "python": "3.12"
    }
