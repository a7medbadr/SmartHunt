from fastapi import APIRouter

from smarthunt.database.session import AsyncSessionLocal
from smarthunt.database.repositories.job_repository import JobRepository

router = APIRouter(prefix="/database", tags=["Database Statistics"])


@router.get("/statistics")
async def database_statistics():
    async with AsyncSessionLocal() as session:
        repo = JobRepository(session)
        jobs = await repo.get_all()

    return {
        "jobs": len(jobs)
    }
