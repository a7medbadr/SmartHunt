from fastapi import APIRouter, Query
from smarthunt.search import search_service

router = APIRouter(prefix="/api/v1/search", tags=["search"])

@router.get("/jobs")
async def search_jobs(
    title: str | None = Query(None, alias="title"),
    location: str | None = Query(None),
    provider: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    return await search_service.search(
        query=title,
        location=location,
        provider=provider,
        page=page,
        limit=limit,
    )
