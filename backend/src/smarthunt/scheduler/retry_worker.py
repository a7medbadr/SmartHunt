from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.failed_job_repository import (
    FailedJobRepository,
)
from smarthunt.scheduler.failed_job_service import (
    failed_scheduler_job_service,
)


class SchedulerRetryWorker:

    def __init__(self):
        self.repository = FailedJobRepository()

    async def process(
        self,
        db: AsyncSession,
    ):

        failed_jobs = await self.repository.list_failed(db)

        processed = []

        for job in failed_jobs:

            updated = await failed_scheduler_job_service.prepare_retry(
                db,
                job,
            )

            processed.append(updated)

        return processed


scheduler_retry_worker = SchedulerRetryWorker()
