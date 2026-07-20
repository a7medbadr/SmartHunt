from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.apply_queue.schemas import (
    ApplyQueueCreate,
    ApplyQueueResponse,
    ApplyQueueStatusUpdate,
)
from smarthunt.apply_queue.service import (
    ApplyQueueInvalidStatusError,
    ApplyQueueNotFoundError,
    apply_queue_service,
)

router = APIRouter(prefix="", tags=["apply-queue"])


@router.post("", response_model=ApplyQueueResponse, status_code=status.HTTP_201_CREATED)
async def add_to_queue(payload: ApplyQueueCreate, db: AsyncSession = Depends(get_db)):
    return await apply_queue_service.add(db, payload)


@router.get("", response_model=List[ApplyQueueResponse])
async def list_queue(db: AsyncSession = Depends(get_db)):
    return await apply_queue_service.list_all(db)


@router.patch("/{item_id}", response_model=ApplyQueueResponse)
async def update_queue_status(
    item_id: int, payload: ApplyQueueStatusUpdate, db: AsyncSession = Depends(get_db)
):
    try:
        return await apply_queue_service.update_status(db, item_id, payload)
    except ApplyQueueNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ApplyQueueInvalidStatusError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_from_queue(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await apply_queue_service.delete(db, item_id)
    except ApplyQueueNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
