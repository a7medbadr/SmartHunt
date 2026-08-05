from __future__ import annotations

from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.domain.job import DiscoveredJob


class JobRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: int):
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_all(self):
        result = await self.session.execute(select(Job))
        return list(result.scalars())

    async def delete(self, job_id: int):

        job = await self.get(job_id)

        if job is None:
            return False

        await self.session.delete(job)
        await self.session.commit()

        return True

    async def exists(
        self,
        source: str,
        title: str,
        location: str | None,
    ) -> bool:

        stmt = (
            select(Job.id)
            .where(Job.source == source)
            .where(Job.title == title)
            .where(Job.location == location)
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def save_discovered_jobs(
        self,
        jobs: list[DiscoveredJob],
    ) -> int:

        inserted = 0

        for item in jobs:

            if await self.exists(
                item.source,
                item.title,
                item.location,
            ):
                continue

            self.session.add(
                Job(
                    title=item.title,
                    company=item.company,
                    location=item.location,
                    description=item.description,
                    requirements=item.requirements,
                    source=item.source,
                    url=item.url,
                    posted_at=item.posted_at,
                )
            )

            inserted += 1

        await self.session.commit()

        return inserted

    async def search_jobs(self, params):

        stmt = select(Job)

        if getattr(params, "title", None):
            stmt = stmt.where(Job.title.ilike(f"%{params.title}%"))

        if getattr(params, "company", None):
            stmt = stmt.where(Job.company.ilike(f"%{params.company}%"))

        if getattr(params, "location", None):
            stmt = stmt.where(Job.location.ilike(f"%{params.location}%"))

        if getattr(params, "provider", None):
            stmt = stmt.where(Job.source.ilike(f"%{params.provider}%"))

        total = (
            await self.session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        sort_name = getattr(
            params,
            "sort",
            "created_at",
        )

        sort_attr = getattr(
            Job,
            sort_name,
            Job.created_at,
        )

        if (
            str(
                getattr(
                    params,
                    "order",
                    "desc",
                )
            ).lower()
            == "asc"
        ):
            stmt = stmt.order_by(asc(sort_attr))
        else:
            stmt = stmt.order_by(desc(sort_attr))

        page = getattr(params, "page", 1)
        limit = getattr(params, "limit", 10)

        stmt = stmt.offset((page - 1) * limit).limit(limit)

        result = await self.session.execute(stmt)

        return list(result.scalars()), total
