from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from smarthunt.database.models.job import Job


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self, provider: str, title: str, location: str) -> bool:
        result = await self.session.execute(
            select(Job).where(
                Job.provider == provider,
                Job.title == title,
                Job.location == location,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save_many(self, jobs: list[dict]) -> int:
        inserted = 0
        for item in jobs:
            if await self.exists(
                item["provider"],
                item["title"],
                item["location"],
            ):
                continue
            self.session.add(Job(**item))
            inserted += 1
        await self.session.commit()
        return inserted

    async def list_all(self):
        result = await self.session.execute(
            select(Job).order_by(Job.score.desc())
        )
        return result.scalars().all()

    async def get_all(self) -> list[Job]:
        result = await self.session.execute(select(Job))
        return list(result.scalars().all())

    async def get(self, job_id: int) -> Job | None:
        result = await self.session.execute(
            select(Job).where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def create(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def delete(self, job_id: int) -> None:
        job = await self.get(job_id)
        if job is not None:
            await self.session.delete(job)
            await self.session.commit()

    async def filter_jobs(
        self,
        keyword: str | None = None,
        company: str | None = None,
        location: str | None = None,
        source: str | None = None,
        page: int = 1,
        size: int = 10,
    ) -> list[Job]:
        query = select(Job)
        if keyword:
            query = query.where(Job.title.ilike(f"%{keyword}%"))
        if company:
            query = query.where(Job.company.ilike(f"%{company}%"))
        if location:
            query = query.where(Job.location.ilike(f"%{location}%"))
        if source:
            query = query.where(Job.source.ilike(f"%{source}%"))
        query = query.offset((page - 1) * size).limit(size)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def sorted_jobs(self, sort_by: str, order: str) -> list[Job]:
        column = getattr(Job, sort_by, Job.id)
        query = select(Job)
        query = query.order_by(column.desc() if order == "desc" else column.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())
