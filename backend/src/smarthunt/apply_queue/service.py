from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.apply_queue.schemas import ApplyQueueCreate, ApplyQueueStatusUpdate

VALID_STATUSES = {"PENDING", "RUNNING", "SUCCESS", "FAILED"}


class ApplyQueueNotFoundError(Exception):
    pass


class ApplyQueueInvalidStatusError(Exception):
    pass


class ApplyQueueService:
    async def add(self, db: AsyncSession, data: ApplyQueueCreate) -> ApplyQueueItem:
        item = ApplyQueueItem(
            job_id=data.job_id,
            provider=data.provider,
            priority=data.priority,
            status="PENDING",
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return item

    async def list_all(self, db: AsyncSession) -> List[ApplyQueueItem]:
        result = await db.execute(
            select(ApplyQueueItem).order_by(
                ApplyQueueItem.priority.desc(), ApplyQueueItem.created_at
            )
        )
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, item_id: int) -> ApplyQueueItem:
        result = await db.execute(select(ApplyQueueItem).where(ApplyQueueItem.id == item_id))
        item = result.scalar_one_or_none()
        if item is None:
            raise ApplyQueueNotFoundError(f"Apply queue item with id {item_id} not found")
        return item

    async def update_status(
        self, db: AsyncSession, item_id: int, data: ApplyQueueStatusUpdate
    ) -> ApplyQueueItem:
        if data.status not in VALID_STATUSES:
            raise ApplyQueueInvalidStatusError(
                f"Invalid status '{data.status}'. Must be one of {sorted(VALID_STATUSES)}"
            )
        item = await self.get(db, item_id)
        item.status = data.status
        item.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        await db.flush()
        await db.refresh(item)
        return item

    async def delete(self, db: AsyncSession, item_id: int) -> None:
        item = await self.get(db, item_id)
        await db.delete(item)
        await db.flush()


apply_queue_service = ApplyQueueService()
