from typing import List, Tuple, Any

from sqlalchemy import select, func, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: int) -> Job | None:
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_all(self) -> List[Job]:
        result = await self.session.execute(select(Job))
        return list(result.scalars().all())

    async def delete(self, job_id: int) -> bool:
        job = await self.get(job_id)
        if job:
            await self.session.delete(job)
            await self.session.commit()
            return True
        return False

    async def exists(self, source: str, title: str, location: str | None) -> bool:
        result = await self.session.execute(
            select(Job).where(
                Job.source == source,
                Job.title == title,
                Job.location == location,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save_many(self, jobs: list[dict]) -> int:
        """Persist job dicts coming from providers. Skips duplicates
        (same source + title + location) and maps 'provider' -> 'source'."""
        inserted = 0
        valid_columns = Job.__table__.columns.keys()

        for item in jobs:
            job_data = item.copy()

            # id is auto-generated (UUID default) — never accept an external id
            job_data.pop("id", None)

            # Map 'provider' to 'source' since the Job model only has 'source'
            if "provider" in job_data:
                job_data["source"] = job_data.pop("provider")

            if not job_data.get("company"):
                job_data["company"] = "N/A"

            if not job_data.get("url"):
                source = job_data.get("source", "unknown")
                title_slug = str(job_data.get("title", "job")).lower().replace(" ", "-")
                job_data["url"] = f"https://{source}.com/jobs/{title_slug}-{inserted}"

            if await self.exists(
                job_data.get("source", ""),
                job_data.get("title", ""),
                job_data.get("location"),
            ):
                continue

            clean_data = {k: v for k, v in job_data.items() if k in valid_columns}

            self.session.add(Job(**clean_data))
            inserted += 1

        await self.session.commit()
        return inserted

    async def search_jobs(self, params: Any) -> Tuple[List[Job], int]:
        query = select(Job)

        # 1. Dynamic Filter Engine
        if getattr(params, "title", None):
            query = query.where(Job.title.ilike(f"%{params.title}%"))
        if getattr(params, "company", None):
            query = query.where(Job.company.ilike(f"%{params.company}%"))
        if getattr(params, "location", None):
            query = query.where(Job.location.ilike(f"%{params.location}%"))
        # Job has 'source', not 'provider' — filter provider queries against it
        if getattr(params, "provider", None):
            query = query.where(Job.source.ilike(f"%{params.provider}%"))

        # Count total matches before applying offset/limit
        count_query = select(func.count()).select_from(query.subquery())
        total_count = (await self.session.execute(count_query)).scalar_one()

        # 2. Safe Sorting Engine (Fallback to created_at or id)
        default_sort_attr = getattr(Job, "created_at", Job.id)
        sort_field = getattr(params, "sort", "created_at")
        if isinstance(sort_field, str) and hasattr(Job, sort_field):
            sort_attr = getattr(Job, sort_field)
        else:
            sort_attr = default_sort_attr

        order_val = str(getattr(params, "order", "desc")).lower()
        direction = desc if order_val == "desc" else asc
        query = query.order_by(direction(sort_attr))

        # 3. Pagination Engine
        page = getattr(params, "page", 1)
        limit = getattr(params, "limit", 10)
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        jobs = result.scalars().all()
        return list(jobs), total_count
