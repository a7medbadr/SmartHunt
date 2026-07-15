from fastapi import FastAPI
from smarthunt.core.lifecycle import lifespan

# المسارات الصحيحة للـ routers
from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.jobs import router as jobs_router
from smarthunt.api.routes.providers import router as providers_router
from smarthunt.api.routes.health import router as health_router

app = FastAPI(lifespan=lifespan)

# تسجيل الـ routers
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(jobs_router, prefix="/api/v1/jobs")
app.include_router(providers_router, prefix="/api/v1/providers")
app.include_router(health_router, prefix="/api/v1/health")
