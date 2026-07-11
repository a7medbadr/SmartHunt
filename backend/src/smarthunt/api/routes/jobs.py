from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.api.schemas import JobCreate, JobResponse
from smarthunt.database.repositories.job_repository import JobRepository

router = APIRouter(prefix="/jobs", tags=["jobs"])

# استخدام Annotated بيمنع الـ B008 وبيخلي الكود مقروء أكتر
DBDeps = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[JobResponse])
async def get_jobs(db: DBDeps):
    """Retrieve all jobs."""
    repository = JobRepository(db)
    return await repository.get_all()


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    db: DBDeps,
):
    """Create a new job."""
    repository = JobRepository(db)

    job_data = payload.model_dump(exclude={"url"})
    db_obj = repository.model(**job_data, url=str(payload.url))

    try:
        job = await repository.create(instance=db_obj)
        return job
    except IntegrityError as err:
        await db.rollback()
        # إضافة 'from err' لحل إيرور B904 وربط الـ Stack Trace بشكل سليم
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A job with this URL already exists.",
        ) from err
