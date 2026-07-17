from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.session import async_session
from smarthunt.database.repositories.job_repository import JobRepository

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/jobs")
async def database_jobs():

    async with async_session() as session:

        repo = JobRepository(session)

        rows = await repo.list_all()

        return {
            "count": len(rows),
            "items": [
                {
                    "id": x.id,
                    "provider": x.provider,
                    "title": x.title,
                    "location": x.location,
                    "salary": x.salary,
                    "score": x.score,
                }
                for x in rows
            ],
        }
