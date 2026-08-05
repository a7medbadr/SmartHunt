from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.dashboard.schemas import DashboardStatisticsResponse
from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job
from smarthunt.favorites.models import FavoriteJob
from smarthunt.providers.registry import provider_registry


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _count(self, model) -> int:
        result = await self.db.execute(select(func.count()).select_from(model))
        return result.scalar_one()

    async def get_statistics(self) -> DashboardStatisticsResponse:
        linkedin_posts_result = await self.db.execute(
            select(func.count()).select_from(Job).where(Job.source == "linkedin_post")
        )
        return DashboardStatisticsResponse(
            jobs=await self._count(Job),
            applications=await self._count(Application),
            favorites=await self._count(FavoriteJob),
            linkedin_posts=linkedin_posts_result.scalar_one(),
            providers=len(provider_registry.providers()),
        )
