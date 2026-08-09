from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.api.schemas import JobCreate, JobResponse
from smarthunt.api.schemas.job import JobReviewStatusUpdate
from smarthunt.applications.repository import ApplicationRepository
from smarthunt.auth.security import get_current_user
from smarthunt.database.models.application import Application
from smarthunt.database.models.user import User
from smarthunt.services import JobService

router = APIRouter(tags=["jobs"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[JobResponse])
async def list_jobs(db: DB):
    return await JobService(db).list_jobs()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, db: DB):
    job = await JobService(db).get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )
    return job


@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    payload: JobCreate,
    db: DB,
    current_user: CurrentUser,
):
    try:
        return await JobService(db).create_job(
            title=payload.title,
            company=payload.company,
            location=payload.location,
            source=payload.source,
            url=str(payload.url),
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job already exists",
        ) from None


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, db: DB):
    deleted = await JobService(db).delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")


@router.patch("/{job_id}/review-status", response_model=JobResponse)
async def update_job_review_status(job_id: int, payload: JobReviewStatusUpdate, db: DB):
    """The owner's own triage of a discovered job — "applied" or
    "not_suitable" — from the discovered-jobs tabs' list view (see
    Job.review_status's docstring). Marking a job "applied" also creates
    a real Application row linked via job_id (skipped if one already
    exists for this job, so toggling applied off then back on doesn't
    pile up duplicates) — this is the "goes to the Applications tab on
    its own" behavior requested 2026-08-09, on top of the lightweight
    review_status flag used for fast list-view filtering."""
    job = await JobService(db).update_review_status(job_id, payload.review_status)
    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if payload.review_status == "applied":
        existing = await db.execute(select(Application).where(Application.job_id == job_id))
        if existing.scalar_one_or_none() is None:
            await ApplicationRepository(db).create(
                job_title=job.title,
                company=job.company,
                url=job.url,
                status="Applied",
                job_id=job.id,
            )

    return job
