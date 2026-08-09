from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.dashboard.schemas import DashboardStatisticsResponse, DashboardTimeseriesResponse
from smarthunt.dashboard.service import DashboardService
from smarthunt.database.session import get_db

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/statistics",
    response_model=DashboardStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Statistics",
)
async def get_dashboard_statistics(db: AsyncSession = Depends(get_db)):
    service = DashboardService(db)
    return await service.get_statistics()


@router.get(
    "/timeseries",
    response_model=DashboardTimeseriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Daily Timeseries",
)
async def get_dashboard_timeseries(
    days: int = Query(default=14, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    service = DashboardService(db)
    return await service.get_timeseries(days=days)
