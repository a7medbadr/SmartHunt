from fastapi import APIRouter, Query
from typing import Optional
from smarthunt.search.service import search_service
from smarthunt.search.schemas import SearchResponse

router = APIRouter()

@router.get("/jobs", response_model=SearchResponse)
async def search_jobs(
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1),
):
    result = await search_service.search_jobs(
        title=title,
        location=location,
        provider=provider,
        page=page,
        limit=limit,
    )
    return {
        "items": result.items,
        "total": result.total,
        "page": result.page,
        "limit": result.limit,
        "pages": result.pages,
    }
