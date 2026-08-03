from datetime import datetime, timezone
from typing import List

import structlog
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.metrics import (
    notifications_sent_total,
    notifications_unread_total,
)
from smarthunt.notifications.channels.email import send_email_message
from smarthunt.notifications.channels.telegram import send_telegram_message
from smarthunt.notifications.models import (
    Notification,
    NotificationStatus,
)
from smarthunt.notifications.schemas import NotificationCreate

logger = structlog.get_logger("smarthunt")


class NotificationNotFoundError(Exception):
    pass


class NotificationService:

    async def create(
        self,
        db: AsyncSession,
        data: NotificationCreate,
    ) -> Notification:

        notification = Notification(
            user_id=data.user_id,
            type=data.type,
            title=data.title,
            message=data.message,
            status=NotificationStatus.SENT.value,
            channel=data.channel,
            priority=data.priority,
            expires_at=data.expires_at,
        )

        db.add(notification)

        await db.flush()
        await db.refresh(notification)

        notifications_sent_total.inc()

        unread = await self.unread_count(db)
        notifications_unread_total.set(unread)

        if data.channel.upper() == "TELEGRAM":
            sent = await send_telegram_message(f"{data.title}\n\n{data.message}")
            if not sent:
                logger.warning(
                    "telegram_notification_not_delivered",
                    notification_id=notification.id,
                )

        if data.channel.upper() == "EMAIL":
            sent = await send_email_message(data.title, data.message)
            if not sent:
                logger.warning(
                    "email_notification_not_delivered",
                    notification_id=notification.id,
                )

        return notification

    async def list_all(
        self,
        db: AsyncSession,
    ) -> List[Notification]:

        result = await db.execute(select(Notification).order_by(Notification.created_at.desc()))

        return list(result.scalars().all())

    async def unread_count(
        self,
        db: AsyncSession,
    ) -> int:

        result = await db.execute(
            select(func.count()).select_from(Notification).where(Notification.read_at.is_(None))
        )

        return int(result.scalar() or 0)

    async def get(
        self,
        db: AsyncSession,
        notification_id: int,
    ) -> Notification:

        result = await db.execute(select(Notification).where(Notification.id == notification_id))

        notification = result.scalar_one_or_none()

        if notification is None:
            raise NotificationNotFoundError(f"Notification with id {notification_id} not found")

        return notification

    async def mark_read(
        self,
        db: AsyncSession,
        notification_id: int,
    ) -> Notification:

        notification = await self.get(db, notification_id)

        notification.status = NotificationStatus.READ.value
        notification.read_at = datetime.now(timezone.utc)

        await db.flush()
        await db.refresh(notification)

        unread = await self.unread_count(db)
        notifications_unread_total.set(unread)

        return notification

    async def mark_all_read(
        self,
        db: AsyncSession,
    ) -> int:

        result = await db.execute(
            update(Notification)
            .where(Notification.read_at.is_(None))
            .values(
                status=NotificationStatus.READ.value,
                read_at=datetime.now(timezone.utc),
            )
        )

        await db.flush()

        unread = await self.unread_count(db)
        notifications_unread_total.set(unread)

        return result.rowcount or 0

    async def cleanup_expired(
        self,
        db: AsyncSession,
    ) -> int:

        result = await db.execute(
            select(Notification).where(
                Notification.expires_at.is_not(None),
                Notification.expires_at < datetime.now(timezone.utc),
            )
        )

        rows = list(result.scalars().all())

        for row in rows:
            await db.delete(row)

        await db.flush()

        unread = await self.unread_count(db)
        notifications_unread_total.set(unread)

        return len(rows)

    async def delete(
        self,
        db: AsyncSession,
        notification_id: int,
    ) -> None:

        notification = await self.get(db, notification_id)

        await db.delete(notification)
        await db.flush()

        unread = await self.unread_count(db)
        notifications_unread_total.set(unread)


notification_service = NotificationService()
