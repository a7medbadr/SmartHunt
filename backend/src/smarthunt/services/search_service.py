import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.matching.services.matcher import match as match_resume

logger = logging.getLogger(__name__)


class SearchService:
    """Service layer for querying jobs discovered and stored in the database."""

    def __init__(self, db_session: Optional[AsyncSession] = None) -> None:
        self.db = db_session
        self.repository = JobRepository(db_session) if db_session is not None else None

    async def search(
        self,
        query: str = "",
        location: str = "",
        page: int = 1,
        limit: int = 10,
        resume_text: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Return all stored jobs; the router applies keyword/location/source
        filtering, sorting, and pagination on top of this result set.

        When `resume_text` is given, each job also gets a `score` (0-100)
        from matching the resume against the job's skills, so the caller
        can filter/sort by real resume-fit instead of a fabricated field."""
        logger.info(f"Searching jobs with query='{query}', location='{location}'")

        jobs = await self.repository.get_all() if self.repository is not None else []

        job_dicts = [
            {
                "id": job.id,
                "title": job.title,
                "location": job.location,
                "company": job.company,
                "source": job.source,
                "url": job.url,
                "requirements": job.requirements,
                "description": job.description,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "posted_at": job.posted_at.isoformat() if job.posted_at else None,
                "post_url": job.post_url,
                "no_sponsorship_signal": job.no_sponsorship_signal,
                "review_status": job.review_status,
                "score": (
                    match_resume(
                        resume_text or "",
                        f"{job.title or ''} {job.description or ''} {job.requirements or ''}",
                    )["score"]
                    if resume_text is not None
                    else None
                ),
            }
            for job in jobs
        ]

        return {
            "jobs": job_dicts,
            "total": len(job_dicts),
            "page": page,
            "limit": limit,
        }

    # Alias for backwards compatibility if needed elsewhere
    search_jobs = search
