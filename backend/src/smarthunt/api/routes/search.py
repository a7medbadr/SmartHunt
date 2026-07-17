from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies.database import get_db
from smarthunt.search.schemas import SearchJobQueryParams
from smarthunt.search.service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/jobs", status_code=status.HTTP_200_OK)
async def search_jobs(
    params: SearchJobQueryParams = Depends(),
    db: AsyncSession = Depends(get_db)
):
    return await SearchService.execute_search(db=db, params=params)


@router.get("/history", status_code=status.HTTP_200_OK)
async def get_search_history(
    limit: int = Query(default=100, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    return await SearchService.get_search_history(db=db, limit=limit)
