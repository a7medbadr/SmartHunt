from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.session import get_db
from smarthunt.recruitment.schemas import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdateStatus,
)
from smarthunt.recruitment.service import RecruitmentService

router = APIRouter(prefix="/api/v1/applications", tags=["applications"])


def get_recruitment_service(
    session: AsyncSession = Depends(get_db),
) -> RecruitmentService:
    return RecruitmentService(session=session)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_application(
    payload: ApplicationCreate,
    service: RecruitmentService = Depends(get_recruitment_service),
) -> ApplicationResponse:
    return await service.create_application(payload)


@router.get("", response_model=List[ApplicationResponse])
async def list_applications(
    service: RecruitmentService = Depends(get_recruitment_service),
) -> List[ApplicationResponse]:
    return await service.list_applications()


@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_status(
    app_id: UUID,
    payload: ApplicationUpdateStatus,
    service: RecruitmentService = Depends(get_recruitment_service),
) -> ApplicationResponse:
    updated = await service.update_status(app_id=app_id, status=payload.status)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
    return updated


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    app_id: UUID,
    service: RecruitmentService = Depends(get_recruitment_service),
) -> None:
    deleted = await service.delete_application(app_id=app_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found",
        )
