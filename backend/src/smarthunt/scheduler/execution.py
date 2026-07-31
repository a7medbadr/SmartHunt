import logging
import traceback
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.failed_job_service import (
    failed_scheduler_job_service,
)
from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate
from smarthunt.scheduler.history.service import (
    scheduler_history_service,
)


logger = logging.getLogger(
    "smarthunt.scheduler.execution"
)


async def execute_scheduler_job(
    db: AsyncSession,
    *,
    provider: str,
    job_reference: str,
    handler,
):

    started = datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )

    try:

        result = await handler()

        await scheduler_history_service.create(
            db,
            SchedulerHistoryCreate(
                provider=provider,
                status="SUCCESS",
                jobs_found=0,
                message=job_reference,
            ),
        )

        return result


    except Exception as exc:

        error = (
            f"{exc}\n"
            f"{traceback.format_exc()}"
        )

        logger.exception(
            "Scheduler job failed: %s",
            job_reference,
        )

        await failed_scheduler_job_service.create(
            db,
            provider=provider,
            job_reference=job_reference,
            error=error,
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


    finally:

        logger.info(
            "Scheduler execution finished: %s started=%s",
            job_reference,
            started,
        )
