from fastapi import APIRouter, Query, Depends, HTTPException
import traceback
import sys
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.resume import Resume
from smarthunt.database.session import get_db
from smarthunt.services.search_service import SearchService
from smarthunt.search.filtering import filter_jobs, sort_jobs, paginate_jobs

router = APIRouter(prefix="", tags=["search"])


async def _get_resume_text(db: AsyncSession) -> str | None:
    """The currently uploaded resume's already-extracted text, straight
    from the DB (the canonical reference — set on upload, see
    resume/api/router.py) rather than re-parsing the file on every
    search call. Single-user app: whichever resume was uploaded most
    recently is "the" resume, regardless of which account uploaded it."""
    result = await db.execute(select(Resume).order_by(Resume.updated_at.desc()).limit(1))
    resume = result.scalar_one_or_none()
    return resume.extracted_text if resume else None


@router.get("/jobs")
async def search_jobs(
    keyword: str | None = Query(None, description="Search keyword in title and description"),
    location: str | None = Query(None, description="Filter jobs by location"),
    source: str | None = Query(None, description="Filter jobs by source provider"),
    title: str | None = Query(None, alias="title"),
    company: str | None = Query(None),
    provider: str | None = Query(None),
    score_min: int | None = Query(
        None, ge=0, le=100, description="Minimum resume-match score (needs an uploaded resume)"
    ),
    score_max: int | None = Query(None, ge=0, le=100),
    sort: str = Query("title", description="Sort field: title, location, source, score, etc."),
    order: str = Query("asc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    session: AsyncSession = Depends(get_db),
):
    try:
        search_service = SearchService(session)
        eff_keyword = keyword if keyword is not None else title
        eff_source = source if source is not None else provider

        # Always compute score (a cheap, rule-based keyword match — no AI
        # call) so the Jobs tab can show a match-% column on every job by
        # default, not only when explicitly sorting/filtering by it.
        resume_text = await _get_resume_text(session)

        res = await search_service.search(
            query=eff_keyword or "",
            company=company,
            location=location or "",
            provider=eff_source or "",
            resume_text=resume_text,
            page=1,
            limit=1000,
        )

        jobs = res.get("jobs", [])

        # 1. التصفية (Filtering)
        filtered_jobs = filter_jobs(
            jobs,
            keyword=eff_keyword,
            location=location,
            source=eff_source,
        )

        if score_min is not None:
            filtered_jobs = [j for j in filtered_jobs if (j.get("score") or 0) >= score_min]
        if score_max is not None:
            filtered_jobs = [j for j in filtered_jobs if (j.get("score") or 0) <= score_max]

        # 2. الترتيب (Sorting)
        sorted_jobs = sort_jobs(
            filtered_jobs,
            sort_by=sort,
            order=order,
        )

        # 3. التقسيم إلى صفحات (Pagination)
        paginated_jobs, total = paginate_jobs(
            sorted_jobs,
            page=page,
            limit=limit,
        )

        return {
            "jobs": paginated_jobs,
            "total": total,
            "page": page,
            "limit": limit,
        }
    except Exception as e:
        print("=" * 60, file=sys.stderr)
        print("!!! [CRITICAL ERROR] In /search/jobs:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
