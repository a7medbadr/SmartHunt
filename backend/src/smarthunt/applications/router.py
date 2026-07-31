import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.applications.repository import ApplicationRepository
from smarthunt.applications.schemas import (
    VALID_STATUSES,
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
)

router = APIRouter(prefix="/applications", tags=["applications"])

DB = Annotated[AsyncSession, Depends(get_db)]


def _validate_status(value: str | None) -> None:
    if value is not None and value not in VALID_STATUSES:
        raise HTTPException(status_code=422, detail="Invalid status")


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(db: DB):
    return await ApplicationRepository(db).list_all()


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(payload: ApplicationCreate, db: DB):
    _validate_status(payload.status)

    return await ApplicationRepository(db).create(
        job_title=payload.job_title,
        company=payload.company,
        url=str(payload.url) if payload.url else None,
        status=payload.status,
    )


@router.patch("/{application_id}", response_model=ApplicationResponse)
async def update_application(application_id: uuid.UUID, payload: ApplicationUpdate, db: DB):
    _validate_status(payload.status)

    repository = ApplicationRepository(db)
    application = await repository.get(application_id)

    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    return await repository.update(
        application,
        job_title=payload.job_title,
        company=payload.company,
        url=str(payload.url) if payload.url else None,
        status=payload.status,
    )


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(application_id: uuid.UUID, db: DB):
    repository = ApplicationRepository(db)
    application = await repository.get(application_id)

    if application is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    await repository.delete(application)
    return None
