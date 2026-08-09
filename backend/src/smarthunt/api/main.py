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


# allow_credentials=True combined with a wildcard origin is a known CORS
# misconfiguration — starlette's CORSMiddleware doesn't literally send
# "*" once credentials are enabled, it reflects the request's actual
# Origin header back as the allowed origin, which means "any site,
# with credentials" (any cookie/browser-credentialed request from any
# origin would be allowed through). Found 2026-08-07 during a security
# audit: BACKEND_CORS_ORIGINS has never been configured in this deployment
# (empty list), so this was live in that exact configuration on the
# publicly-routed backend, which also serves the Swagger UI by default
# (enable_docs=True). Credentials are now only allowed once specific
# trusted origins are actually configured; the wildcard fallback for the
# common case (no origins configured) stays permissive for anonymous
# requests but never reflects credentials.
_cors_origins = settings.BACKEND_CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_credentials=bool(_cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


setup_metrics(app)


app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)
