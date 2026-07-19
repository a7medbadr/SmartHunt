from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.apply_queue.models import ApplyQueueItem
from smarthunt.apply_queue.schemas import ApplyQueueResponse
from smarthunt.browser.playwright.engine import playwright_engine


class AutoApplyWorkerNotFoundError(Exception):
    pass


class AutoApplyWorker:
    async def process_next(self, db: AsyncSession) -> Optional[ApplyQueueItem]:
        result = await db.execute(
            select(ApplyQueueItem)
            .where(ApplyQueueItem.status == "PENDING")
            .order_by(ApplyQueueItem.priority.desc(), ApplyQueueItem.created_at)
            .limit(1)
        )
        item = result.scalar_one_or_none()
        if item is None:
            return None

        item.status = "RUNNING"
        await db.flush()

        await playwright_engine.apply(job_url=f"job:{item.job_id}")

        item.status = "SUCCESS"
        await db.flush()
        await db.refresh(item)
        return item

    async def process_all(self, db: AsyncSession) -> List[ApplyQueueItem]:
        processed: List[ApplyQueueItem] = []
        while True:
            item = await self.process_next(db)
            if item is None:
                break
            processed.append(item)
        return processed

    async def retry_failed(self, db: AsyncSession) -> List[ApplyQueueItem]:
        result = await db.execute(select(ApplyQueueItem).where(ApplyQueueItem.status == "FAILED"))
        failed_items = list(result.scalars().all())

        retried: List[ApplyQueueItem] = []
        for item in failed_items:
            item.status = "RUNNING"
            await db.flush()

            await playwright_engine.apply(job_url=f"job:{item.job_id}")

            item.status = "SUCCESS"
            await db.flush()
            await db.refresh(item)
            retried.append(item)

        return retried

    async def cancel(self, db: AsyncSession, item_id: int) -> ApplyQueueItem:
        result = await db.execute(select(ApplyQueueItem).where(ApplyQueueItem.id == item_id))
        item = result.scalar_one_or_none()
        if item is None:
            raise AutoApplyWorkerNotFoundError(f"Apply queue item with id {item_id} not found")

        item.status = "FAILED"
        await db.flush()
        await db.refresh(item)
        return item


auto_apply_worker = AutoApplyWorker()

router = APIRouter(prefix="", tags=["apply-worker"])


@router.post("/next", response_model=Optional[ApplyQueueResponse])
async def process_next(db: AsyncSession = Depends(get_db)):
    return await auto_apply_worker.process_next(db)


@router.post("/all", response_model=List[ApplyQueueResponse])
async def process_all(db: AsyncSession = Depends(get_db)):
    return await auto_apply_worker.process_all(db)


@router.post("/retry", response_model=List[ApplyQueueResponse])
async def retry_failed(db: AsyncSession = Depends(get_db)):
    return await auto_apply_worker.retry_failed(db)


@router.post("/cancel/{item_id}", response_model=ApplyQueueResponse)
async def cancel(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await auto_apply_worker.cancel(db, item_id)
    except AutoApplyWorkerNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
