from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.events.repository import event_repository
from smarthunt.events.schemas import EventResponse

router = APIRouter(
    prefix="/events",
    tags=["events"],
)


@router.get(
    "",
    response_model=List[EventResponse],
)
async def list_events(
    db: AsyncSession = Depends(get_db),
):
    return await event_repository.list_all(db)
