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
from smarthunt.providers.api.router import router as new_providers_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # عند تشغيل التطبيق: تهيئة قاعدة البيانات
    await db_session.create_engine()
    yield
    # عند إغلاق التطبيق: قفل الاتصال بقاعدة البيانات
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
