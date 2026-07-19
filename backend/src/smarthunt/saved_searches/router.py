from fastapi import APIRouter, HTTPException, status
from typing import List
from smarthunt.saved_searches.schemas import SavedSearchCreate, SavedSearchResponse
from smarthunt.saved_searches.service import saved_search_service

router = APIRouter(prefix="", tags=["saved-searches"])


@router.post("", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(payload: SavedSearchCreate):
    if not payload.name or not payload.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Name cannot be empty",
        )
    return saved_search_service.create(payload)


@router.get("", response_model=List[SavedSearchResponse])
async def list_saved_searches():
    return saved_search_service.list_all()


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(search_id: int):
    success = saved_search_service.delete(search_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Saved search with id {search_id} not found",
        )
    return None
