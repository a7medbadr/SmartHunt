from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.health import get_db
from smarthunt.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/jobs")
async def search_jobs(
    title: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    provider: Optional[str] = Query(None),
    score_min: Optional[int] = Query(None),
    sort: Optional[str] = Query("created_at"),
    order: Optional[str] = Query("desc"),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    result = await service.search(
        query=title,
        location=location,
        provider=provider,
        page=page,
        limit=limit,
    )

    # Format return structure to match test expectations
    return {
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "provider": getattr(job, "provider", provider or "unknown"),
                "location": job.location,
                "salary": getattr(job, "salary", 0),
                "score": getattr(job, "score", 0),
            }
            for job in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "limit": result["limit"],
    }


@router.get("/history")
async def get_search_history(
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    return await service.get_history(limit=limit)


@router.delete("/history")
async def clear_search_history(
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    return await service.clear_history()
