from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.failed_job_service import (
    failed_scheduler_job_service,
)
from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate
from smarthunt.scheduler.history.service import (
    scheduler_history_service,
)


class SchedulerExecutionService:

    async def execute(
        self,
        db: AsyncSession,
        *,
        provider: str,
        job_reference: str,
        handler,
    ):

        try:
            result = await handler()

            await scheduler_history_service.create(
                db,
                SchedulerHistoryCreate(
                    provider=provider,
                    status="SUCCESS",
                    jobs_found=len(result) if result else 0,
                    message="Scheduler execution completed",
                ),
            )

            return result

        except Exception as exc:

            await failed_scheduler_job_service.create(
                db,
                provider=provider,
                job_reference=job_reference,
                error=str(exc),
            )

            await scheduler_history_service.create(
                db,
                SchedulerHistoryCreate(
                    provider=provider,
                    status="FAILED",
                    jobs_found=0,
                    message=str(exc),
                ),
            )

            raise


scheduler_execution_service = SchedulerExecutionService()
