from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from smarthunt.core.config import settings
from smarthunt.database import session as db_session
from smarthunt.api.routes import (
    auth_router,
    health_router,
    jobs_router,
    providers_router as old_providers_router,
    scheduler_router,
)
from smarthunt.search.router import router as search_router
from smarthunt.search.history_router import router as search_history_router
from smarthunt.search.database_router import router as database_jobs_router
from smarthunt.search.cache_router import router as cache_router
from smarthunt.providers.api.router import router as new_providers_router
from smarthunt.providers.health.router import router as provider_health_router
from smarthunt.api.routes.database import router as database_router
from smarthunt.api.routes.provider_statistics import router as provider_statistics_router
from smarthunt.api.routes.search_metrics import router as search_metrics_router
from smarthunt.api.routes.database_statistics import router as database_statistics_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_session.create_engine()
    yield
    await db_session.close_engine()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url="/api/v1/openapi.json",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1/health")
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(old_providers_router, prefix="/api/v1/providers_old", tags=["Providers_Old"])
app.include_router(scheduler_router, prefix="/api/v1/scheduler", tags=["Scheduler"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
app.include_router(new_providers_router, prefix="/api/v1/providers", tags=["Providers"])
app.include_router(provider_health_router, prefix="/api/v1/providers", tags=["Provider Health"])
app.include_router(provider_statistics_router, prefix="/api/v1")
app.include_router(search_metrics_router, prefix="/api/v1")
app.include_router(database_statistics_router, prefix="/api/v1")
app.include_router(search_history_router)
app.include_router(database_jobs_router)
app.include_router(cache_router, prefix="/api/v1")
app.include_router(database_router, prefix="/api/v1")
