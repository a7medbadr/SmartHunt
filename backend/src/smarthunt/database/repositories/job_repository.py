from sqlalchemy import Select, select

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
