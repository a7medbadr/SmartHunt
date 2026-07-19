from sqlalchemy.ext.asyncio import AsyncSession
from smarthunt.dashboard.schemas import DashboardStatisticsResponse

class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_statistics(self) -> DashboardStatisticsResponse:
        return DashboardStatisticsResponse(
            jobs=0,
            applications=0,
            favorites=0,
            saved_searches=0,
            providers=0
        )
