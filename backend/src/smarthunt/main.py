import structlog
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from smarthunt.middleware.request_id import RequestIDMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from .core.config import settings
from smarthunt.logging.config import configure_logging
from .api.routes import auth, health, jobs, providers
from smarthunt.matching.api.router import router as matching_router
from smarthunt.resume.api import list_router
from smarthunt.resume.api.router import router as resume_router

logger = structlog.get_logger()

# Default API Version Prefix
API_V1_STR = "/api/v1"

# Create a master router
api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(providers.router, prefix="/providers", tags=["providers"])
api_router.include_router(resume_router, prefix="/resume", tags=["resume"])

# إضافة المسارات الجديدة داخل الـ Master Router المركزي لتجنب مشاكل الـ Prefixes
api_router.include_router(matching_router, prefix="/matching", tags=["Matching"])
api_router.include_router(list_router.router, prefix="/resumes", tags=["Resume"])

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url=f"{API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
allow_origins = ["*"] if settings.app_debug else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)

# Include API Routers (كل شيء تحت /api/v1)
app.include_router(api_router, prefix=API_V1_STR)

# Initialize and expose Prometheus Metrics safely without crashing on nested routers
Instrumentator(
    should_group_untemplated=False,
    should_ignore_untemplated=True
).instrument(app).expose(
    app,
    endpoint=f"{API_V1_STR}/metrics",
    tags=["Metrics"]
)

@app.on_event("startup")
async def startup_event():
    await logger.ainfo("Starting up SmartHunt Backend Application", project_name=settings.app_name)

@app.on_event("shutdown")
async def shutdown_event():
    await logger.ainfo("Shutting down SmartHunt Backend Application")
