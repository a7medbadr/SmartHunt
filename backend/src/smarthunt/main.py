from fastapi import FastAPI

from smarthunt.recruitment.api import router as recruitment_router
from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.jobs import router as jobs_router
from smarthunt.api.routes.health import router as health_router
from smarthunt.matching.api.routes import router as matching_router
from smarthunt.resume.api.router import router as resume_router
from smarthunt.search.router import router as search_router
from smarthunt.cover_letter.api import router as cover_letter_router

app = FastAPI(title="SmartHunt API")

app.include_router(recruitment_router)
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(jobs_router, prefix="/api/v1/jobs")
app.include_router(health_router, prefix="/api/v1")
app.include_router(matching_router, prefix="/api/v1")
app.include_router(resume_router, prefix="/api/v1/resume")
app.include_router(search_router, prefix="/api/v1/search")
app.include_router(cover_letter_router)


@app.get("/")
def read_root():
    return {"message": "Welcome to SmartHunt API"}
