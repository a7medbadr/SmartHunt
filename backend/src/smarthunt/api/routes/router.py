from fastapi import APIRouter

from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.health import router as health_router
from smarthunt.api.routes.jobs import router as jobs_router
from smarthunt.career.router import router as career_router
from smarthunt.cover_letter.api import router as cover_letter_router
from smarthunt.cover_letter.reviewer.router import router as cover_letter_reviewer_router
from smarthunt.job_notes.api import router as job_notes_router
from smarthunt.job_tags.api import router as job_tags_router
from smarthunt.matching.api.router import router as matching_router
from smarthunt.recommendation.router import router as recommendation_router
from smarthunt.recruitment.api import router as recruitment_router
from smarthunt.resume.api.router import router as resume_router
from smarthunt.resume.reviewer.router import router as resume_reviewer_router
from smarthunt.search.router import router as search_router
from smarthunt.saved_searches.router import router as saved_searches_router
from smarthunt.favorites.router import router as favorites_router
from smarthunt.dashboard.api import router as dashboard_router
from smarthunt.activity.api import router as activity_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(recruitment_router, prefix="", tags=["recruitment"])
api_router.include_router(jobs_router, prefix="/jobs", tags=["jobs"])
api_router.include_router(recommendation_router, prefix="", tags=["recommendation"])
api_router.include_router(cover_letter_router, prefix="/cover-letter", tags=["cover-letter"])
api_router.include_router(cover_letter_reviewer_router, prefix="/cover-letter", tags=["cover-letter"])
api_router.include_router(job_notes_router, prefix="/job-notes", tags=["job-notes"])
api_router.include_router(job_tags_router, prefix="/job-tags", tags=["job-tags"])
api_router.include_router(matching_router, prefix="/matching", tags=["matching"])
api_router.include_router(career_router, prefix="/career", tags=["career"])
api_router.include_router(resume_router, prefix="/resume", tags=["resume"])
api_router.include_router(resume_reviewer_router, prefix="/resume", tags=["resume"])
api_router.include_router(search_router, prefix="/search", tags=["search"])
api_router.include_router(saved_searches_router, prefix="/saved-searches", tags=["saved-searches"])
api_router.include_router(favorites_router, prefix="/favorites", tags=["favorites"])
api_router.include_router(dashboard_router, tags=["dashboard"])
api_router.include_router(activity_router, tags=["activity"])
