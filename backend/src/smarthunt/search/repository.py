from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def all(self):
        result = await self.session.execute(select(Job))
        return result.scalars().all()

    async def create(self, **kwargs):
        job = Job(**kwargs)
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job
