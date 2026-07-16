from fastapi import APIRouter, Query, HTTPException
import traceback
import sys
from smarthunt.search import search_service

router = APIRouter(prefix="", tags=["search"])

@router.get("/jobs")
async def search_jobs(
    title: str | None = Query(None, alias="title"),
    location: str | None = Query(None),
    provider: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    try:
        res = await search_service.search(
            query=title,
            location=location,
            provider=provider,
            page=page,
            limit=limit,
        )
        return res
    except Exception as e:
        # هنطبع الـ stack trace كامل في الترمنال عشان نشوف السطر اللي ضرب فين بالظبط
        print("="*60, file=sys.stderr)
        print("!!! [CRITICAL ERROR] In /search/jobs:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("="*60, file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
