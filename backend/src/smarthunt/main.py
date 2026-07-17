import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from smarthunt.api.routes import health
from smarthunt.core.config import settings
from smarthunt.database.session import engine
from smarthunt.matching.api.router import router as matching_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SmartHunt application...")
    yield
    logger.info("Shutting down SmartHunt application...")
    if engine:
        await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(matching_router, prefix=settings.API_V1_STR, tags=["matching"])


@app.get("/")
async def root():
    return {
        "message": "Welcome to SmartHunt API",
        "docs": "/docs",
        "health": f"{settings.API_V1_STR}/health/live",
    }
