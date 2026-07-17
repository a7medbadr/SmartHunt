from collections import Counter
from fastapi import APIRouter

from smarthunt.database.session import AsyncSessionLocal
from smarthunt.database.repositories.job_repository import JobRepository

router = APIRouter(prefix="/providers", tags=["Provider Statistics"])


@router.get("/statistics")
async def statistics():
    if not AsyncSessionLocal:
        return {}

    async with AsyncSessionLocal() as session:
        repo = JobRepository(session)
        jobs = await repo.get_all()

    providers = []
    for job in jobs:
        if isinstance(job, dict):
            p = job.get("provider")
        else:
            p = getattr(job, "provider", None)
        if p:
            providers.append(p)

    stats = Counter(providers)
    return dict(stats)
