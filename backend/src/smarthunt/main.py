from fastapi import FastAPI

from smarthunt.api.routes import jobs_router
from smarthunt.api.routes.providers import router as providers_router
from smarthunt.core.config import get_settings
from smarthunt.core.lifecycle import lifespan
from smarthunt.core.logging import configure_logging

configure_logging()

settings = get_settings()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )

    # تسجيل الـ Routers تحت الـ prefix المحدد
    app.include_router(jobs_router, prefix="/api/v1")
    app.include_router(providers_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "project": settings.app_name,
            "version": settings.app_version,
            "status": "running",
        }

    @app.get("/health")
    async def health():
        return {
            "status": "healthy",
        }

    return app


app = create_application()
