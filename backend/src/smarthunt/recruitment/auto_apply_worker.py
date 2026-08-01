from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.apply_queue.schemas import ApplyQueueResponse
from smarthunt.browser.playwright.engine import playwright_engine
from smarthunt.database.models.job import Job
from smarthunt.logging.logger import logger
from smarthunt.notifications.schemas import NotificationCreate
from smarthunt.notifications.service import NotificationService
from smarthunt.scheduler.locks.service import scheduler_lock_service

notification_service = NotificationService()


class AutoApplyWorkerNotFoundError(Exception):
    pass


class AutoApplyWorker:

    async def process_next(
        self,
        db: AsyncSession,
    ) -> Optional[ApplyQueueItem]:

        result = await db.execute(
            select(ApplyQueueItem)
            .where(ApplyQueueItem.status == "PENDING")
            .order_by(
                ApplyQueueItem.priority.desc(),
                ApplyQueueItem.created_at,
            )
            .limit(1)
        )

        item = result.scalar_one_or_none()

        if item is None:
            return None

        return await self.process_item(db, item)

    async def process_item(
        self,
        db: AsyncSession,
        item: ApplyQueueItem,
    ) -> Optional[ApplyQueueItem]:
        """Runs one specific queue item through the real apply flow.
        Split out from process_next() so a targeted "apply to this job
        right now" caller (the quick-apply endpoint) can drive a known
        item directly, instead of racing whatever process_next()'s
        priority/created_at ordering happens to pick next."""

        locked = await scheduler_lock_service.acquire(
            db,
            str(item.job_id),
        )

        if not locked:
            return None

        item.status = "RUNNING"
        await db.flush()

        job_result = await db.execute(select(Job).where(Job.id == item.job_id))
        job = job_result.scalar_one_or_none()

        try:

            if job is None or not job.url:
                item.status = "FAILED"
            else:
                result = await playwright_engine.apply(
                    job_url=job.url,
                    provider=item.provider,
                    db=db,
                )

                item.status = "SUCCESS" if result.get("status") == "SUCCESS" else "FAILED"

                if item.status == "SUCCESS":
                    try:
                        await self._notify_success(db, job)
                    except Exception:
                        # The application itself already succeeded — a
                        # notification hiccup (e.g. Telegram down) must
                        # not flip a real success back to FAILED.
                        logger.exception(
                            f"Failed to send auto-apply notification for job_id={job.id}"
                        )

        except Exception:

            item.status = "FAILED"

        finally:

            await scheduler_lock_service.release(
                db,
                str(item.job_id),
            )

        await db.flush()
        await db.refresh(item)

        return item

    async def _notify_success(self, db: AsyncSession, job: Job) -> None:
        """Fulfils the product's core promise: applications happen
        unattended, then the owner is told afterward, not asked to click
        "apply" themselves. Uses the TELEGRAM channel so this starts
        delivering for real the moment TELEGRAM_BOT_TOKEN/
        TELEGRAM_CHAT_ID are configured — NotificationService already
        no-ops the send (while still recording the in-app notification)
        when they're unset, so this is safe to fire unconditionally."""

        await notification_service.create(
            db,
            NotificationCreate(
                type="SUCCESS",
                title=f"تم التقديم تلقائيًا: {job.title}",
                message=f"قدّمنا تلقائيًا على وظيفة {job.title} في {job.company}"
                f"{f' ({job.location})' if job.location else ''}.\n{job.url or ''}",
                channel="TELEGRAM",
                priority="HIGH",
            ),
        )

    async def process_all(
        self,
        db: AsyncSession,
    ) -> List[ApplyQueueItem]:

        processed: List[ApplyQueueItem] = []

        while True:

            item = await self.process_next(
                db,
            )

            if item is None:
                break

            processed.append(item)

        return processed

    async def retry_failed(
        self,
        db: AsyncSession,
    ) -> List[ApplyQueueItem]:

        result = await db.execute(select(ApplyQueueItem).where(ApplyQueueItem.status == "FAILED"))

        failed_items = list(result.scalars().all())

        retried: List[ApplyQueueItem] = []

        for item in failed_items:

            item.status = "PENDING"
            await db.flush()

            processed = await self.process_next(
                db,
            )

            if processed is not None:
                retried.append(processed)

        return retried

    async def cancel(
        self,
        db: AsyncSession,
        item_id: int,
    ) -> ApplyQueueItem:

        result = await db.execute(select(ApplyQueueItem).where(ApplyQueueItem.id == item_id))

        item = result.scalar_one_or_none()

        if item is None:
            raise AutoApplyWorkerNotFoundError(f"Apply queue item with id {item_id} not found")

        item.status = "FAILED"

        await db.flush()
        await db.refresh(item)

        return item


auto_apply_worker = AutoApplyWorker()

router = APIRouter(
    prefix="",
    tags=["apply-worker"],
)


@router.post(
    "/next",
    response_model=Optional[ApplyQueueResponse],
)
async def process_next(
    db: AsyncSession = Depends(get_db),
):
    return await auto_apply_worker.process_next(db)


@router.post(
    "/all",
    response_model=List[ApplyQueueResponse],
)
async def process_all(
    db: AsyncSession = Depends(get_db),
):
    return await auto_apply_worker.process_all(db)


@router.post(
    "/retry",
    response_model=List[ApplyQueueResponse],
)
async def retry_failed(
    db: AsyncSession = Depends(get_db),
):
    return await auto_apply_worker.retry_failed(db)


@router.post(
    "/cancel/{item_id}",
    response_model=ApplyQueueResponse,
)
async def cancel(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await auto_apply_worker.cancel(
            db,
            item_id,
        )
    except AutoApplyWorkerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
