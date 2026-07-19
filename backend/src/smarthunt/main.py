from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from smarthunt.api.routes import api_router
from smarthunt.core.config import settings
from smarthunt.core.lifespan import lifespan


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


Instrumentator().instrument(app).expose(app)

app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }
