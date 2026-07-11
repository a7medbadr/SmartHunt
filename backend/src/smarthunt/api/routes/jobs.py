from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.api.schemas import JobCreate, JobResponse
from smarthunt.services import DiscoveryService, JobService

router = APIRouter(prefix="/jobs", tags=["jobs"])

# الـ Type Alias النظيف للـ Dependency Injection
DB = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=list[JobResponse])
async def list_jobs(db: DB):
    """List all jobs."""
    return await JobService(db).list_jobs()


@router.get("/discover")
async def discover_jobs(
    db: DB,
    keyword: str,
    location: str | None = None,
):
    """Discover new jobs using DiscoveryService."""
    return await DiscoveryService(db).discover(
        keyword=keyword,
        location=location,
    )


@router.get("/filter", response_model=list[JobResponse])
async def filter_jobs(
    db: DB,
    keyword: str | None = None,
    company: str | None = None,
    location: str | None = None,
    source: str | None = None,
    page: int = 1,
    size: int = 20,
):
    """Filter jobs by multiple criteria."""
    return await JobService(db).filter_jobs(
        keyword,
        company,
        location,
        source,
        page,
        size,
    )


@router.get("/sorted", response_model=list[JobResponse])
async def sorted_jobs(
    db: DB,
    sort_by: str = "created_at",
    order: str = "desc",
):
    """Get sorted jobs."""
    return await JobService(db).sorted_jobs(
        sort_by,
        order,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: DB):
    """Get a specific job by ID."""
    job = await JobService(db).get_job(job_id)
    if job is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(payload: JobCreate, db: DB):
    """Create a new job."""
    try:
        return await JobService(db).create_job(
            title=payload.title,
            company=payload.company,
            location=payload.location,
            source=payload.source,
            url=str(payload.url),
        )
    except IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job already exists",
        ) from err


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, db: DB):
    """Delete a job by ID."""
    deleted = await JobService(db).delete_job(job_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.get("/search/", response_model=list[JobResponse])
async def search_jobs(db: DB, keyword: str = Query(..., min_length=2)):
    """Search jobs by keyword."""
    return await JobService(db).repository.search(keyword)


@router.get("/page/", response_model=list[JobResponse])
async def paginated_jobs(
    db: DB,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
):
    """Get a paginated list of jobs."""
    return await JobService(db).repository.get_page(
        page=page,
        page_size=size,
    )
