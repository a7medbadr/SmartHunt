from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.notifications.schemas import NotificationCreate, NotificationResponse
from smarthunt.notifications.service import (
    NotificationNotFoundError,
    notification_service,
)

router = APIRouter(prefix="", tags=["notifications"])


@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(payload: NotificationCreate, db: AsyncSession = Depends(get_db)):
    return await notification_service.create(db, payload)


@router.get("", response_model=List[NotificationResponse])
async def list_notifications(db: AsyncSession = Depends(get_db)):
    return await notification_service.list_all(db)


@router.patch("/{notification_id}/read")
async def mark_notification_read(notification_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await notification_service.mark_read(db, notification_id)
    except NotificationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return {"status": "updated"}


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await notification_service.delete(db, notification_id)
    except NotificationNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
