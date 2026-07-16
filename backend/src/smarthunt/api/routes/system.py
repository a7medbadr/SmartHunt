from fastapi import APIRouter
from smarthunt.core.config import settings

router = APIRouter()

@router.get("/summary")
async def summary():
    return {
        "status": "healthy",
        "database": "up",
        "api": "up",
        "metrics": "up"
    }

@router.get("/config")
async def get_config():
    return {
        "Debug": settings.app_debug if hasattr(settings, "app_debug") else True,
        "Providers Enabled": ["SmartHunt", "LinkedIn", "GulfTalent"],
        "Metrics": True,
        "Scheduler": True,
        "Database": "PostgreSQL",
        "JWT Expire": settings.jwt_expire_minutes if hasattr(settings, "jwt_expire_minutes") else 1440,
        "Upload Path": "/app/uploads/resumes",
        "Max Upload": "5MB",
        "Allowed Extensions": [".pdf", ".docx", ".txt"]
    }
