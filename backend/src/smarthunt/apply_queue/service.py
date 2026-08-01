from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.apply_queue.schemas import (
    ApplyQueueCreate,
    ApplyQueueStatusUpdate,
    QuickApplyRequest,
)
from smarthunt.database.models.job import Job

VALID_STATUSES = {"PENDING", "RUNNING", "SUCCESS", "FAILED"}

PROVIDER_URL_MARKERS = {
    "linkedin.com": "linkedin",
    "bayt.com": "bayt",
    "gulftalent.com": "gulftalent",
    "wuzzuf.net": "wuzzuf",
}


def infer_provider(url: str) -> str:
    lowered = url.lower()
    for marker, provider in PROVIDER_URL_MARKERS.items():
        if marker in lowered:
            return provider
    return "linkedin"


class ApplyQueueNotFoundError(Exception):
    pass


class ApplyQueueInvalidStatusError(Exception):
    pass


class ApplyQueueService:
    async def quick_apply(self, db: AsyncSession, data: QuickApplyRequest) -> ApplyQueueItem:
        """Lets the owner paste any job link and apply to it right away,
        rather than only being able to queue jobs SmartHunt discovered
        itself. Reuses an existing Job row for the same url if one
        already exists (e.g. it was actually discovered), otherwise
        creates a minimal one so the real apply flow — which needs a
        Job to look up a url from — has something to work with."""

        from smarthunt.recruitment.auto_apply_worker import auto_apply_worker

        existing = await db.execute(select(Job).where(Job.url == data.url))
        job = existing.scalar_one_or_none()

        if job is None:
            job = Job(
                title=data.title,
                company=data.company,
                url=data.url,
                source="manual",
            )
            db.add(job)
            await db.flush()
            await db.refresh(job)

        item = ApplyQueueItem(
            job_id=job.id,
            provider=data.provider or infer_provider(data.url),
            priority=10,
            status="PENDING",
        )
        db.add(item)
        await db.flush()
        await db.refresh(item)

        processed = await auto_apply_worker.process_item(db, item)

        return processed if processed is not None else item

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
