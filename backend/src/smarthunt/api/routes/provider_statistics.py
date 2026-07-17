from collections import Counter

from fastapi import APIRouter

from smarthunt.database.session import AsyncSessionLocal
from smarthunt.database.repositories.job_repository import JobRepository

router = APIRouter(prefix="/providers", tags=["Provider Statistics"])


@router.get("/statistics")
async def statistics():
    async with AsyncSessionLocal() as session:
        repo = JobRepository(session)
        jobs = await repo.get_all()

    stats = Counter(job.provider for job in jobs)

    return dict(stats)
