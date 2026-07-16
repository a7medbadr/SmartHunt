from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import مباشر لتفادي مشاكل الـ __init__.py والملفات الناقصة
from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.health import router as health_router
from smarthunt.api.routes.jobs import router as jobs_router
from smarthunt.api.routes.providers import router as providers_router
from smarthunt.api.routes.system import router as system_router
from smarthunt.search.router import router as search_router

app = FastAPI(
    title="SmartHunt API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# تسجيل الـ Routers الأساسية المتاحة فعلياً
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(health_router, prefix="/api/v1/health", tags=["Health"])
app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(providers_router, prefix="/api/v1/providers", tags=["Providers"])
app.include_router(system_router, prefix="/api/v1/system", tags=["System"])

# تسجيل موديول البحث اللي شغالين عليه
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])

@app.get("/api/v1/version")
async def get_version():
    return {
        "name": "SmartHunt",
        "version": "1.0.0",
        "git": "latest",
        "environment": "sandbox",
        "python": "3.12"
    }
