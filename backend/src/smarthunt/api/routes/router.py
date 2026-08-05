from fastapi import APIRouter

from smarthunt.activity.api import router as activity_router
from smarthunt.ai.api import router as ai_router
from smarthunt.audit.router import router as audit_router
from smarthunt.apply_queue.router import router as apply_queue_router
from smarthunt.applications.router import router as applications_router
from smarthunt.api.routes.auth import router as auth_router
from smarthunt.api.routes.health import router as health_router
from smarthunt.api.routes.jobs import router as jobs_router
from smarthunt.api.routes.system import router as system_router
from smarthunt.browser.playwright.router import router as playwright_router
from smarthunt.browser.session.router import router as browser_session_router
from smarthunt.career.router import router as career_router
from smarthunt.cover_letter.api import router as cover_letter_router
from smarthunt.cover_letter.reviewer.router import (
    router as cover_letter_reviewer_router,
)
from smarthunt.dashboard.api import router as dashboard_router
from smarthunt.discovery.router import router as discovery_router
from smarthunt.email_apply.router import router as email_apply_router
from smarthunt.linkedin_monitor.router import router as linkedin_monitor_router
from smarthunt.events.router import router as events_router
from smarthunt.favorites.router import router as favorites_router
from smarthunt.idempotency.router import router as idempotency_router
from smarthunt.job_notes.api import router as job_notes_router
from smarthunt.job_tags.api import router as job_tags_router
from smarthunt.matching.api.router import router as matching_router
from smarthunt.notifications.router import router as notifications_router
from smarthunt.providers.health.router import (
    router as provider_health_router,
)
from smarthunt.providers.settings.router import (
    router as provider_settings_router,
)
from smarthunt.recommendation.router import router as recommendation_router
from smarthunt.recruitment.api import router as recruitment_router
from smarthunt.recruitment.auto_apply_worker import (
    router as apply_worker_router,
)
from smarthunt.resume.api.router import router as resume_router
from smarthunt.resume.reviewer.router import (
    router as resume_reviewer_router,
)
from smarthunt.saved_searches.router import router as saved_searches_router
from smarthunt.scheduler.history.router import (
    router as scheduler_history_router,
)
from smarthunt.scheduler.locks.router import (
    router as scheduler_locks_router,
)
from smarthunt.scheduler.failed_job_router import (
    router as scheduler_failed_jobs_router,
)
from smarthunt.search.router import router as search_router
from smarthunt.search.metrics_router import router as search_metrics_router
from smarthunt.settings.router import router as settings_router

api_router = APIRouter()


api_router.include_router(
    health_router,
    tags=["health"],
)

api_router.include_router(
    system_router,
    tags=["system"],
)

api_router.include_router(
    ai_router,
    tags=["ai"],
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"],
)

api_router.include_router(
    recruitment_router,
    tags=["recruitment"],
)

api_router.include_router(
    applications_router,
    tags=["applications"],
)

api_router.include_router(
    email_apply_router,
    tags=["email-apply"],
)

api_router.include_router(
    linkedin_monitor_router,
    tags=["linkedin-monitor"],
)

api_router.include_router(
    jobs_router,
    prefix="/jobs",
    tags=["jobs"],
)

api_router.include_router(
    recommendation_router,
    tags=["recommendation"],
)

api_router.include_router(
    cover_letter_router,
    prefix="/cover-letter",
    tags=["cover-letter"],
)

api_router.include_router(
    cover_letter_reviewer_router,
    prefix="/cover-letter",
    tags=["cover-letter"],
)

api_router.include_router(
    job_notes_router,
    prefix="/job-notes",
    tags=["job-notes"],
)

api_router.include_router(
    job_tags_router,
    prefix="/job-tags",
    tags=["job-tags"],
)

api_router.include_router(
    matching_router,
    prefix="/matching",
    tags=["matching"],
)

api_router.include_router(
    career_router,
    prefix="/career",
    tags=["career"],
)

api_router.include_router(
    resume_router,
    prefix="/resume",
    tags=["resume"],
)

api_router.include_router(
    resume_reviewer_router,
    prefix="/resume",
    tags=["resume"],
)

api_router.include_router(
    search_router,
    prefix="/search",
    tags=["search"],
)

api_router.include_router(
    search_metrics_router,
    tags=["search-metrics"],
)

api_router.include_router(
    saved_searches_router,
    prefix="/saved-searches",
    tags=["saved-searches"],
)

api_router.include_router(
    favorites_router,
    prefix="/favorites",
    tags=["favorites"],
)

api_router.include_router(
    dashboard_router,
    tags=["dashboard"],
)

api_router.include_router(
    discovery_router,
    tags=["discovery"],
)

api_router.include_router(
    activity_router,
    tags=["activity"],
)

api_router.include_router(
    audit_router,
    tags=["audit"],
)

api_router.include_router(
    events_router,
    tags=["events"],
)

api_router.include_router(
    notifications_router,
    prefix="/notifications",
    tags=["notifications"],
)

api_router.include_router(
    settings_router,
    prefix="/settings",
    tags=["settings"],
)

api_router.include_router(
    provider_health_router,
    prefix="/providers/health",
    tags=["provider-health"],
)

api_router.include_router(
    provider_settings_router,
    tags=["providers"],
)

api_router.include_router(
    scheduler_history_router,
    prefix="/scheduler/history",
    tags=["scheduler-history"],
)

api_router.include_router(
    scheduler_locks_router,
    prefix="/scheduler/locks",
    tags=["scheduler-locks"],
)

api_router.include_router(
    scheduler_failed_jobs_router,
    prefix="/scheduler",
    tags=["scheduler-failed-jobs"],
)

api_router.include_router(
    idempotency_router,
    prefix="/idempotency",
    tags=["idempotency"],
)

api_router.include_router(
    apply_queue_router,
    prefix="/apply-queue",
    tags=["apply-queue"],
)

api_router.include_router(
    browser_session_router,
    prefix="/browser/session",
    tags=["browser-session"],
)

api_router.include_router(
    playwright_router,
    prefix="/browser/playwright",
    tags=["playwright"],
)

api_router.include_router(
    apply_worker_router,
    prefix="/apply-worker",
    tags=["apply-worker"],
)
