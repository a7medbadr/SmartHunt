from sqlalchemy import Select, func, select, asc, desc

from smarthunt.database.models.job import Job
from smarthunt.database.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, session):
        super().__init__(session, Job)

    async def search(
        self,
        keyword: str,
    ) -> list[Job]:
        stmt: Select[tuple[Job]] = select(Job).where(
            Job.title.ilike(f"%{keyword}%")
            | Job.company.ilike(f"%{keyword}%")
            | Job.location.ilike(f"%{keyword}%")
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_page(
        self,
        *,
        page: int,
        page_size: int,
    ) -> list[Job]:
        stmt = select(Job).offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total number of jobs."""
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def filter_jobs(
        self,
        keyword: str | None,
        company: str | None,
        location: str | None,
        source: str | None,
        page: int,
        size: int,
    ) -> list[Job]:
        """Filter jobs with multiple criteria and pagination."""
        stmt = select(self.model)

        if keyword:
            stmt = stmt.where(self.model.title.ilike(f"%{keyword}%"))

        if company:
            stmt = stmt.where(self.model.company.ilike(f"%{company}%"))

        if location:
            stmt = stmt.where(self.model.location.ilike(f"%{location}%"))

        if source:
            stmt = stmt.where(self.model.source.ilike(f"%{source}%"))

        stmt = stmt.offset((page - 1) * size).limit(size)

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def sorted_jobs(
        self,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[Job]:
        """Get sorted jobs."""
        column = getattr(self.model, sort_by)

        stmt = select(self.model)

        if order == "asc":
            stmt = stmt.order_by(asc(column))
        else:
            stmt = stmt.order_by(desc(column))

        result = await self.session.execute(stmt)

        return list(result.scalars().all())
