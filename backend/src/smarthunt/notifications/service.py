from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.notifications.models import Notification
from smarthunt.notifications.schemas import NotificationCreate


class NotificationNotFoundError(Exception):
    pass


class NotificationService:
    async def create(self, db: AsyncSession, data: NotificationCreate) -> Notification:
        notification = Notification(
            title=data.title,
            message=data.message,
            type=data.type,
        )
        db.add(notification)
        await db.flush()
        await db.refresh(notification)
        return notification

    async def list_all(self, db: AsyncSession) -> List[Notification]:
        result = await db.execute(
            select(Notification).order_by(Notification.created_at.desc())
        )
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, notification_id: int) -> Notification:
        result = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        notification = result.scalar_one_or_none()
        if notification is None:
            raise NotificationNotFoundError(
                f"Notification with id {notification_id} not found"
            )
        return notification

    async def mark_read(self, db: AsyncSession, notification_id: int) -> Notification:
        notification = await self.get(db, notification_id)
        notification.is_read = True
        await db.flush()
        await db.refresh(notification)
        return notification

    async def delete(self, db: AsyncSession, notification_id: int) -> None:
        notification = await self.get(db, notification_id)
        await db.delete(notification)
        await db.flush()


notification_service = NotificationService()
