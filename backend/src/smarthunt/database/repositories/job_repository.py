from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.database.repositories.base import BaseRepository


class JobRepository(BaseRepository[Job]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Job)

    async def get_by_url(self, url: str) -> Job | None:
        stmt = select(Job).where(Job.url == url)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
