from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.activity.models import ActivityType
from smarthunt.activity.service import log_activity
from smarthunt.api.dependencies import get_db
from smarthunt.favorites.schemas import FavoriteJobCreate, FavoriteJobResponse
from smarthunt.favorites.service import (
    FavoriteAlreadyExistsError,
    FavoriteNotFoundError,
    favorites_service,
)

router = APIRouter(prefix="", tags=["favorites"])


@router.post("", response_model=FavoriteJobResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(payload: FavoriteJobCreate, db: AsyncSession = Depends(get_db)):
    try:
        favorite = await favorites_service.add_favorite(db, payload)
    except FavoriteAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await log_activity(
        db,
        ActivityType.FAVORITE_ADDED,
        f"إضافة وظيفة رقم {payload.job_id} للمفضلة",
    )

    return favorite


@router.get("", response_model=List[FavoriteJobResponse])
async def list_favorites(db: AsyncSession = Depends(get_db)):
    return await favorites_service.list_favorites(db)


@router.delete("/{job_id}")
async def delete_favorite(job_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await favorites_service.delete_favorite(db, job_id)
    except FavoriteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"status": "deleted"}
