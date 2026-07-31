import platform

from fastapi import APIRouter

from smarthunt.core.config import settings

router = APIRouter(
    prefix="/system",
    tags=["system"],
)


@router.get("/version")
async def version():
    return {
        "application": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.app_env,
        "python": f"{platform.python_version_tuple()[0]}.{platform.python_version_tuple()[1]}",
        "build": settings.build_version,
    }
