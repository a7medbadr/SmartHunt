from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.history.models import SchedulerHistory
from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate


class SchedulerHistoryService:
    async def create(self, db: AsyncSession, data: SchedulerHistoryCreate) -> SchedulerHistory:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        record = SchedulerHistory(
            provider=data.provider,
            started_at=now,
            finished_at=now,
            status=data.status,
            jobs_found=data.jobs_found,
            message=data.message,
        )
        db.add(record)
        await db.flush()
        await db.refresh(record)
        return record

    async def list_all(self, db: AsyncSession) -> List[SchedulerHistory]:
        result = await db.execute(
            select(SchedulerHistory).order_by(SchedulerHistory.started_at.desc())
        )
        return list(result.scalars().all())

    async def latest(self, db: AsyncSession) -> Optional[SchedulerHistory]:
        result = await db.execute(
            select(SchedulerHistory).order_by(SchedulerHistory.started_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


scheduler_history_service = SchedulerHistoryService()
