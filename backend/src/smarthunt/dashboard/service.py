from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.dashboard.schemas import DashboardStatisticsResponse
from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job
from smarthunt.favorites.models import FavoriteJob
from smarthunt.providers.registry import provider_registry
from smarthunt.saved_searches.models import SavedSearch


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _count(self, model) -> int:
        result = await self.db.execute(select(func.count()).select_from(model))
        return result.scalar_one()

    async def get_statistics(self) -> DashboardStatisticsResponse:
        return DashboardStatisticsResponse(
            jobs=await self._count(Job),
            applications=await self._count(Application),
            favorites=await self._count(FavoriteJob),
            saved_searches=await self._count(SavedSearch),
            providers=len(provider_registry.providers()),
        )
