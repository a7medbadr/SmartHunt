from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.failed_job import FailedSchedulerJob


class FailedSchedulerJobService:

    async def create(
        self,
        db: AsyncSession,
        *,
        provider: str,
        job_reference: str,
        error: str,
    ) -> FailedSchedulerJob:

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        record = FailedSchedulerJob(
            provider=provider,
            job_reference=job_reference,
            status="FAILED",
            retry_count=0,
            last_error=error,
            created_at=now,
            updated_at=now,
        )

        db.add(record)

        await db.flush()
        await db.refresh(record)

        return record


    async def increment_retry(
        self,
        db: AsyncSession,
        record: FailedSchedulerJob,
    ) -> FailedSchedulerJob:

        record.retry_count += 1
        record.updated_at = datetime.now(timezone.utc).replace(
            tzinfo=None
        )

        await db.flush()
        await db.refresh(record)

        return record


failed_scheduler_job_service = FailedSchedulerJobService()
