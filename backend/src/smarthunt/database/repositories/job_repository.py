from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from smarthunt.database.models.job import Job


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self, source: str, title: str, location: str) -> bool:
        result = await self.session.execute(
            select(Job).where(
                Job.source == source,
                Job.title == title,
                Job.location == location,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save_many(self, jobs: list[dict]) -> int:
        inserted = 0
        valid_columns = Job.__table__.columns.keys()

        for item in jobs:
            job_data = item.copy()

            # Remove explicit 'id' if present so database manages auto-increment primary key
            job_data.pop("id", None)

            # Map 'provider' to 'source' if needed
            if "provider" in job_data and "source" not in job_data:
                job_data["source"] = job_data.pop("provider")

            # Fallback for required non-null fields
            if not job_data.get("company"):
                job_data["company"] = "N/A"

            # Fallback for url if missing or empty
            if not job_data.get("url"):
                source = job_data.get("source", "unknown")
                title_slug = job_data.get("title", "job").lower().replace(" ", "-")
                job_data["url"] = f"https://{source}.com/jobs/{title_slug}-{inserted}"

            # Check existence
            if await self.exists(
                job_data.get("source", ""),
                job_data.get("title", ""),
                job_data.get("location", ""),
            ):
                continue

            # Filter data to only include valid columns for the Job model
            clean_data = {k: v for k, v in job_data.items() if k in valid_columns}

            self.session.add(Job(**clean_data))
            inserted += 1

        await self.session.commit()
        return inserted

    async def list_all(self):
        result = await self.session.execute(
            select(Job).order_by(Job.id.desc())
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
