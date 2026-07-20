from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.metrics.scheduler_lock import (
    scheduler_lock_acquired_total,
    scheduler_lock_conflicts_total,
    scheduler_lock_expired_total,
)
from smarthunt.scheduler.locks.models import SchedulerLock


class SchedulerLockService:

    DEFAULT_TIMEOUT = 300

    async def acquire(
        self,
        db: AsyncSession,
        job_id: str,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> bool:

        await self.cleanup_expired(db)

        existing = await db.execute(
            select(SchedulerLock).where(
                SchedulerLock.job_id == job_id
            )
        )

        if existing.scalar_one_or_none():

            scheduler_lock_conflicts_total.inc()
            return False

        now = datetime.now(timezone.utc).replace(
            tzinfo=None
        )

        lock = SchedulerLock(
            job_id=job_id,
            owner_id=str(uuid4()),
            acquired_at=now,
            expires_at=now + timedelta(seconds=timeout),
        )

        db.add(lock)
        await db.flush()

        scheduler_lock_acquired_total.inc()

        return True

    async def release(
        self,
        db: AsyncSession,
        job_id: str,
    ):

        await db.execute(
            delete(SchedulerLock).where(
                SchedulerLock.job_id == job_id
            )
        )

        await db.flush()

    async def cleanup_expired(
        self,
        db: AsyncSession,
    ):

        now = datetime.now(timezone.utc).replace(
            tzinfo=None
        )

        result = await db.execute(
            delete(SchedulerLock).where(
                SchedulerLock.expires_at < now
            )
        )

        if result.rowcount:
            scheduler_lock_expired_total.inc(
                result.rowcount
            )

        await db.flush()

    async def active(
        self,
        db: AsyncSession,
    ):

        await self.cleanup_expired(db)

        result = await db.execute(
            select(SchedulerLock).order_by(
                SchedulerLock.acquired_at
            )
        )

        return list(result.scalars().all())


scheduler_lock_service = SchedulerLockService()
