from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.database.repositories.job_repository import JobRepository


class JobService:
    def __init__(self, session: AsyncSession):
        self.repository = JobRepository(session)

    async def list_jobs(self) -> list[Job]:
        return await self.repository.get_all()

    async def get_job(self, job_id: int) -> Job | None:
        return await self.repository.get(job_id)

    async def create_job(
        self,
        *,
        title: str,
        company: str,
        location: str,
        source: str,
        url: str,
    ) -> Job:
        job = Job(
            title=title,
            company=company,
            location=location,
            source=source,
            url=url,
        )

        try:
            return await self.repository.create(job)
        except IntegrityError:
            await self.repository.session.rollback()
            raise

    async def delete_job(self, job_id: int) -> bool:
        job = await self.repository.get(job_id)

        if job is None:
            return False

        await self.repository.delete(job_id)

        return True

    async def filter_jobs(
        self,
        keyword: str | None,
        company: str | None,
        location: str | None,
        source: str | None,
        page: int,
        size: int,
    ):
        return await self.repository.filter_jobs(
            keyword=keyword,
            company=company,
            location=location,
            source=source,
            page=page,
            size=size,
        )

    async def sorted_jobs(
        self,
        sort_by: str,
        order: str,
    ):
        return await self.repository.sorted_jobs(
            sort_by,
            order,
        )
