from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.job_tags.schemas import JobTagCreate, JobTagResponse
from smarthunt.job_tags.service import (
    JobTagAlreadyExistsError,
    JobTagNotFoundError,
    job_tag_service,
)

router = APIRouter(prefix="", tags=["job-tags"])


@router.post("", response_model=JobTagResponse, status_code=status.HTTP_201_CREATED)
async def add_job_tag(payload: JobTagCreate, db: AsyncSession = Depends(get_db)):
    try:
        return await job_tag_service.add_tag(db, payload)
    except JobTagAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{job_id}", response_model=List[JobTagResponse])
async def list_job_tags(job_id: int, db: AsyncSession = Depends(get_db)):
    return await job_tag_service.list_tags_by_job(db, job_id)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await job_tag_service.delete_tag(db, tag_id)
    except JobTagNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
