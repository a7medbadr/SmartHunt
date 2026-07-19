from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate, SchedulerHistoryResponse
from smarthunt.scheduler.history.service import scheduler_history_service

router = APIRouter(prefix="", tags=["scheduler-history"])


@router.post("", response_model=SchedulerHistoryResponse, status_code=201)
async def create_scheduler_history(payload: SchedulerHistoryCreate, db: AsyncSession = Depends(get_db)):
    return await scheduler_history_service.create(db, payload)


@router.get("/latest", response_model=Optional[SchedulerHistoryResponse])
async def latest_scheduler_history(db: AsyncSession = Depends(get_db)):
    return await scheduler_history_service.latest(db)


@router.get("", response_model=List[SchedulerHistoryResponse])
async def list_scheduler_history(db: AsyncSession = Depends(get_db)):
    return await scheduler_history_service.list_all(db)
