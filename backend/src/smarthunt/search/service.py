from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.search.pipeline import SearchPipeline


class SearchService:

    def __init__(self, session: AsyncSession):
        self.pipeline = SearchPipeline()
        self.repo = JobRepository(session)

    async def search(self, **filters):

        jobs = await self.pipeline.search(**filters)

        await self.repo.save_many(jobs)

        return jobs
