from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.saved_searches.schemas import SavedSearchCreate, SavedSearchResponse
from smarthunt.saved_searches.service import (
    SavedSearchNotFoundError,
    saved_search_service,
)

router = APIRouter(prefix="", tags=["saved-searches"])


@router.post("", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(payload: SavedSearchCreate, db: AsyncSession = Depends(get_db)):
    return await saved_search_service.create(db, payload)


@router.get("", response_model=List[SavedSearchResponse])
async def list_saved_searches(db: AsyncSession = Depends(get_db)):
    return await saved_search_service.list_all(db)


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(search_id: int, db: AsyncSession = Depends(get_db)):
    try:
        await saved_search_service.delete(db, search_id)
    except SavedSearchNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return None
