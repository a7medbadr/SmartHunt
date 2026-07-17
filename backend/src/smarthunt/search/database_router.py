from fastapi import APIRouter

from smarthunt.database import session as db_session
from smarthunt.database.repositories.job_repository import JobRepository

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/jobs")
async def jobs():
    async with db_session.AsyncSessionLocal() as session:
        repo = JobRepository(session)
        rows = await repo.list_all()
        return {
            "count": len(rows),
            "items": [
                {
                    "id": job.id,
                    "provider": getattr(job, "source", None),
                    "title": job.title,
                    "location": job.location,
                    "salary": getattr(job, "salary", None),
                    "score": getattr(job, "score", None),
                }
                for job in rows
            ],
        }
