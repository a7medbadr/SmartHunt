from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.session import get_db as get_session
from smarthunt.search.repository import JobRepository

router = APIRouter(
    prefix="/api/v1/database",
    tags=["Database Jobs"],
)


@router.get("/jobs")
async def jobs(
    session: AsyncSession = Depends(get_session),
):
    repo = JobRepository(session)

    jobs = await repo.all()

    return {
        "count": len(jobs),
        "items": [
            {
                "id": job.id,
                "title": job.title,
                "provider": job.provider,
                "location": job.location,
            }
            for job in jobs
        ],
    }
