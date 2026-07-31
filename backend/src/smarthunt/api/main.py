from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from smarthunt.api.routes import api_router
from smarthunt.core.config import settings
from smarthunt.core.lifespan import lifespan
from smarthunt.metrics import setup_metrics
from smarthunt.middleware.rate_limit import RateLimitMiddleware
from smarthunt.middleware.request_id import RequestIDMiddleware
from smarthunt.middleware.request_logging import RequestLoggingMiddleware
from smarthunt.middleware.security_headers import SecurityHeadersMiddleware
from smarthunt.shared.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    lifespan=lifespan,
)


app.add_exception_handler(
    HTTPException,
    http_exception_handler,
)


app.add_exception_handler(
    Exception,
    unhandled_exception_handler,
)


if settings.app_env != "test":
    app.add_middleware(
        RateLimitMiddleware,
        requests_limit=100,
        window_seconds=60,
    )


app.add_middleware(
    SecurityHeadersMiddleware,
)


app.add_middleware(
    RequestIDMiddleware,
)


app.add_middleware(
    RequestLoggingMiddleware,
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
