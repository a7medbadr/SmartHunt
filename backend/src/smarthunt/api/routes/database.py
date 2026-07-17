from fastapi import APIRouter

from smarthunt.database import session as db_session
from smarthunt.database.repositories.job_repository import JobRepository

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/jobs")
async def database_jobs():
    async with db_session.AsyncSessionLocal() as session:
        repo = JobRepository(session)
        rows = await repo.list_all()
        return {
            "count": len(rows),
            "items": [
                {
                    "id": x.id,
                    "provider": getattr(x, "source", None),
                    "title": x.title,
                    "location": x.location,
                    "salary": getattr(x, "salary", None),
                    "score": getattr(x, "score", None),
                }
                for x in rows
            ],
        }
