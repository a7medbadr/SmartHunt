from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.metrics.failed_jobs import (
    scheduler_failed_jobs_retry_total,
    scheduler_failed_jobs_total,
)
from smarthunt.scheduler.failed_job import FailedSchedulerJob
from smarthunt.scheduler.failed_job_repository import FailedJobRepository


class FailedSchedulerJobService:

    MAX_RETRIES = 3

    BASE_BACKOFF_SECONDS = 60

    def __init__(self):
        self.repository = FailedJobRepository()

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

        result = await self.repository.create(
            db,
            record,
        )

        scheduler_failed_jobs_total.inc()

        return result

    async def can_retry(
        self,
        record: FailedSchedulerJob,
    ) -> bool:

        return record.retry_count < self.MAX_RETRIES

    async def prepare_retry(
        self,
        db: AsyncSession,
        record: FailedSchedulerJob,
    ) -> FailedSchedulerJob:

        if not await self.can_retry(record):
            record.status = "FAILED_FINAL"

        else:
            record.retry_count += 1
            record.status = "RETRY_PENDING"

            scheduler_failed_jobs_retry_total.inc()

        record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)

        await db.flush()
        await db.refresh(record)

        return record

    async def mark_running(
        self,
        db: AsyncSession,
        record: FailedSchedulerJob,
    ):

        record.status = "RUNNING"

        await db.flush()

        return record

    async def mark_success(
        self,
        db: AsyncSession,
        record: FailedSchedulerJob,
    ):

        record.status = "SUCCESS"

        await db.flush()

        return record


failed_scheduler_job_service = FailedSchedulerJobService()
