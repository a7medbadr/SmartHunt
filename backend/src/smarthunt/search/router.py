from fastapi import APIRouter, Query
from smarthunt.search.service import search_service
from smarthunt.search.schemas import SearchResponse

router = APIRouter()

@router.get("/jobs", response_model=SearchResponse)
async def search_jobs(
    title: str = Query(None),
    location: str = Query(None),
    provider: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    return await search_service.search_jobs(
        title=title,
        location=location,
        provider=provider,
        page=page,
        limit=limit
    )
