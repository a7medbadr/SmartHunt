from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.scheduler.failed_job import FailedSchedulerJob


class FailedJobRepository:

    async def create(
        self,
        db: AsyncSession,
        job: FailedSchedulerJob,
    ) -> FailedSchedulerJob:

        db.add(job)
        await db.flush()
        await db.refresh(job)

        return job


    async def list_failed(
        self,
        db: AsyncSession,
    ) -> list[FailedSchedulerJob]:

        result = await db.execute(
            select(FailedSchedulerJob)
            .order_by(FailedSchedulerJob.created_at.desc())
        )

        return list(result.scalars().all())


    async def get(
        self,
        db: AsyncSession,
        job_id: int,
    ) -> FailedSchedulerJob | None:

        result = await db.execute(
            select(FailedSchedulerJob)
            .where(
                FailedSchedulerJob.id == job_id
            )
        )

        return result.scalar_one_or_none()
