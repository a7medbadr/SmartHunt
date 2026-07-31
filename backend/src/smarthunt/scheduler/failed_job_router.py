from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.session import get_db
from smarthunt.scheduler.failed_job_repository import FailedJobRepository


router = APIRouter()

repository = FailedJobRepository()


@router.get(
    "/failed-jobs",
    tags=["scheduler"],
)
async def list_failed_scheduler_jobs(
    db: AsyncSession = Depends(get_db),
):
    return await repository.list_failed(db)
