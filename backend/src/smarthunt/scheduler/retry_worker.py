from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job import FailedSchedulerJob
from smarthunt.scheduler.failed_job_repository import (
    FailedJobRepository,
)
from smarthunt.scheduler.failed_job_service import (
    failed_scheduler_job_service,
)

# Maps a scheduled discovery job's `job_reference` back to the query it
# should re-run. Owned here (not scheduler/jobs.py) so both that module
# and this one can import it without a circular dependency.
TOPIC_QUERIES = {
    "python": "python developer",
    "linux": "linux administrator",
    "devops": "devops engineer",
}


class SchedulerRetryWorker:
    """Actually retries FAILED scheduler jobs, up to MAX_RETRIES, instead
    of just flagging them as retry-eligible and leaving them there."""

    def __init__(self):
        self.repository = FailedJobRepository()

    async def process(
        self,
        db: AsyncSession,
    ):
        result = await db.execute(
            select(FailedSchedulerJob).where(FailedSchedulerJob.status == "FAILED")
        )
        failed_jobs = list(result.scalars().all())

        processed = []

        for job in failed_jobs:
            updated = await failed_scheduler_job_service.prepare_retry(db, job)

            if updated.status == "RETRY_PENDING":
                query = TOPIC_QUERIES.get(updated.job_reference)

                if query is None:
                    # Don't know how to re-run this job type — don't get
                    # stuck retrying it forever.
                    updated.status = "FAILED_FINAL"
                    await db.flush()
                else:
                    await failed_scheduler_job_service.mark_running(db, updated)

                    try:
                        await DiscoveryService(db).discover(
                            query=query,
                            provider=updated.provider,
                        )
                        updated = await failed_scheduler_job_service.mark_success(db, updated)
                    except Exception as exc:
                        updated = await failed_scheduler_job_service.mark_failed(
                            db, updated, str(exc)
                        )

            processed.append(updated)

        return processed


scheduler_retry_worker = SchedulerRetryWorker()
