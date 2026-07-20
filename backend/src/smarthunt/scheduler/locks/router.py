from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.scheduler.locks.schemas import SchedulerLockResponse
from smarthunt.scheduler.locks.service import (
    scheduler_lock_service,
)

router = APIRouter(
    prefix="",
    tags=["scheduler-locks"],
)


@router.get(
    "",
    response_model=List[SchedulerLockResponse],
)
async def active_scheduler_locks(
    db: AsyncSession = Depends(get_db),
):
    return await scheduler_lock_service.active(
        db,
    )
