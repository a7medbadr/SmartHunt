from contextlib import asynccontextmanager

from fastapi import FastAPI

from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.health import router as health_router
from smarthunt.api.routes.jobs import router as jobs_router
from smarthunt.database.session import close_engine, create_engine
from smarthunt.search.router import router as search_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # هيتنفذ عند startup
    await create_engine()
    yield
    # هيتنفذ عند shutdown
    await close_engine()


app = FastAPI(title="SmartHunt API", version="1.0.0", lifespan=lifespan)

app.include_router(health_router, prefix="/api/v1/health", tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(jobs_router, prefix="/api/v1/jobs", tags=["Jobs"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])


@app.get("/")
async def root():
    return {"message": "Welcome to SmartHunt API"}
