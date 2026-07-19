from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.dashboard.schemas import DashboardStatisticsResponse
from smarthunt.dashboard.service import DashboardService
from smarthunt.database.session import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get(
    "/statistics",
    response_model=DashboardStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Statistics"
)
async def get_dashboard_statistics(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_statistics()
