from fastapi import APIRouter, HTTPException, status
from typing import List
from smarthunt.favorites.schemas import FavoriteJobCreate, FavoriteJobResponse
from smarthunt.favorites.service import favorites_service, FavoriteAlreadyExistsError

router = APIRouter(prefix="", tags=["favorites"])


@router.post("", response_model=FavoriteJobResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(payload: FavoriteJobCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Job title cannot be empty",
        )
    try:
        return favorites_service.add_favorite(payload)
    except FavoriteAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=List[FavoriteJobResponse])
async def list_favorites():
    return favorites_service.list_favorites()


@router.delete("/{fav_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_favorite(fav_id: str):
    success = favorites_service.delete_favorite(fav_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Favorite with id or job_id '{fav_id}' not found",
        )
    return None
