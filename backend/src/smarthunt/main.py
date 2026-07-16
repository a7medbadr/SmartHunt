from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from smarthunt.api.routes import auth, health, jobs, providers, system, matching
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

# تسجيل الـ Routers الأساسية
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["Providers"])
app.include_router(system.router, prefix="/api/v1/system", tags=["System"])
app.include_router(matching.router, prefix="/api/v1/matching", tags=["Matching"])

# تسجيل موديول البحث الجديد
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
