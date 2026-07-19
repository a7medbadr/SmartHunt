from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.activity.schemas import ActivityCreate, ActivityResponse
from smarthunt.activity.service import ActivityService
from smarthunt.database.session import get_db

router = APIRouter(prefix="/activity", tags=["Activity"])

@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Activity"
)
async def create_activity(
    data: ActivityCreate,
    db: AsyncSession = Depends(get_db)
):
    service = ActivityService(db)
    return await service.create_activity(data)

@router.get(
    "",
    response_model=List[ActivityResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Recent Activities"
)
async def get_recent_activities(
    db: AsyncSession = Depends(get_db)
):
    service = ActivityService(db)
    return await service.get_recent_activities(limit=20)
