from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.jobs import router as jobs_router
from smarthunt.api.routes.providers import router as providers_router
from smarthunt.api.routes.scheduler import router as scheduler_router

__all__ = [
    "jobs_router",
    "providers_router",
    "scheduler_router",
    "auth_router",
]
