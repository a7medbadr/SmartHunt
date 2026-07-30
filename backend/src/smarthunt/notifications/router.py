from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
)
from smarthunt.notifications.service import (
    NotificationNotFoundError,
    notification_service,
)

router = APIRouter(
    prefix="",
    tags=["notifications"],
)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    payload: NotificationCreate,
    db: AsyncSession = Depends(get_db),
):
    return await notification_service.create(db, payload)


@router.get(
    "",
    response_model=List[NotificationResponse],
)
async def list_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    unread_only: bool = False,
    notification_type: str | None = None,
    channel: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
):
    notifications = await notification_service.list_all(db)

    if unread_only:
        notifications = [
            n for n in notifications
            if n.read_at is None
        ]

    if notification_type:
        notifications = [
            n for n in notifications
            if n.type == notification_type
        ]

    if channel:
        notifications = [
            n for n in notifications
            if n.channel == channel
        ]

    if status_filter:
        notifications = [
            n for n in notifications
            if n.status == status_filter
        ]

    start = (page - 1) * page_size
    end = start + page_size

    return notifications[start:end]


@router.get("/unread-count")
async def unread_count(
    db: AsyncSession = Depends(get_db),
):
    return {
        "count": await notification_service.unread_count(db),
    }


@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        await notification_service.mark_read(
            db,
            notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return {
        "status": "updated",
    }


@router.post("/read-all")
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
):
    updated = await notification_service.mark_all_read(db)

    return {
        "updated": updated,
    }


@router.post("/cleanup")
async def cleanup_expired_notifications(
    db: AsyncSession = Depends(get_db),
):
    deleted = await notification_service.cleanup_expired(db)

    return {
        "deleted": deleted,
    }


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        await notification_service.delete(
            db,
            notification_id,
        )
    except NotificationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
