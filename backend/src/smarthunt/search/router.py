from fastapi import APIRouter, Query, Depends, HTTPException
import traceback
import sys
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.session import get_db
from smarthunt.services.search_service import SearchService

router = APIRouter(prefix="", tags=["search"])


@router.get("/jobs")
async def search_jobs(
    title: str | None = Query(None, alias="title"),
    location: str | None = Query(None),
    provider: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    try:
        search_service = SearchService(session)
        res = await search_service.search(
            query=title,
            location=location,
            provider=provider,
            page=page,
            limit=limit,
        )
        return res
    except Exception as e:
        print("=" * 60, file=sys.stderr)
        print("!!! [CRITICAL ERROR] In /search/jobs:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        raise HTTPException(
            status_code=500, detail=f"Internal Server Error: {str(e)}"
        )
