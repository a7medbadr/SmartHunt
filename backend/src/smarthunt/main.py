from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from smarthunt.api.routes import api_router
from smarthunt.core.config import settings
from smarthunt.core.lifespan import lifespan
from smarthunt.metrics import setup_metrics
from smarthunt.middleware.rate_limit import RateLimitMiddleware
from smarthunt.middleware.request_id import RequestIDMiddleware
from smarthunt.middleware.security_headers import SecurityHeadersMiddleware


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


app.add_middleware(
    SecurityHeadersMiddleware,
)


app.add_middleware(
    RequestIDMiddleware,
)


app.add_middleware(
    RateLimitMiddleware,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


setup_metrics(app)


app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "application": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
