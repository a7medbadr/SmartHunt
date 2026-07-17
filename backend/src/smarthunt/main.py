from fastapi import FastAPI

# Core Routes
from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.jobs import router as jobs_router

# Feature Routers
from smarthunt.matching.api.router import router as matching_router
from smarthunt.resume.api.router import router as resume_router
from smarthunt.search.router import router as search_router

app = FastAPI(
    title="SmartHunt API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/api/v1/openapi.json",
)

# Register Routers with full prefixes
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(jobs_router, prefix="/api/v1/jobs")
app.include_router(matching_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1/resume")
app.include_router(search_router, prefix="/api/v1/search")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
