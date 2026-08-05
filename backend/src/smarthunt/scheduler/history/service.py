from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.history.models import SchedulerHistory
from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate

# Once the log passes this many rows, it's trimmed back down to the most
# recent ARCHIVE_KEEP_COUNT — added 2026-08-04 per explicit request so
# the run-history table doesn't grow unbounded with every scheduled job
# (several run every hour). Not a strict sliding-window cap (which would
# trim on every single insert) — it only fires once the count actually
# crosses the threshold, then drops hard down to the last 10 rather than
# just back under 100, so this doesn't re-trigger on almost every insert
# once near the limit.
ARCHIVE_THRESHOLD = 100
ARCHIVE_KEEP_COUNT = 10


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

        await self._archive_if_over_threshold(db)

        return record

    async def _archive_if_over_threshold(self, db: AsyncSession) -> None:
        total = await db.scalar(select(func.count()).select_from(SchedulerHistory))
        if total is None or total <= ARCHIVE_THRESHOLD:
            return

        keep_ids_result = await db.execute(
            select(SchedulerHistory.id)
            .order_by(SchedulerHistory.started_at.desc())
            .limit(ARCHIVE_KEEP_COUNT)
        )
        keep_ids = [row[0] for row in keep_ids_result.all()]

        await db.execute(
            SchedulerHistory.__table__.delete().where(SchedulerHistory.id.not_in(keep_ids))
        )
        await db.flush()

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
