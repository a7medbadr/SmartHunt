from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.api.schemas import JobCreate, JobResponse
from smarthunt.auth.security import get_current_user
from smarthunt.database.models.user import User
from smarthunt.services import JobService

router = APIRouter(tags=["jobs"])

DB = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("", response_model=list[JobResponse])
async def list_jobs(db: DB):
    return await JobService(db).list_jobs()


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

