from typing import Optional, List, Dict, Any
from types import SimpleNamespace
from sqlalchemy.ext.asyncio import AsyncSession
from smarthunt.database.repositories.job_repository import JobRepository


class SearchService:
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
        self.job_repo = JobRepository(session) if session else JobRepository()

    async def search(
        self,
        query: str | None = None,
        company: str | None = None,
        location: str | None = None,
        provider: str | None = None,
        salary_min: int | None = None,
        salary_max: int | None = None,
        score_min: int | None = None,
        score_max: int | None = None,
        sort: str = "score",
        order: str = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:

        # 1. إعداد الـ params كـ Namespace لتوافق مع JobRepository.search_jobs(params)
        params = SimpleNamespace(
            title=query,
            company=company,
            location=location,
            provider=provider,
            sort=sort,
            order=order,
            page=page,
            limit=limit,
        )

        # 2. جلب البيانات من الـ Repository
        db_jobs, db_total = await self.job_repo.search_jobs(params)

        # تحويل موديلات الـ ORM لـ Dicts لسهولة الفلترة والـ Processing
        jobs: List[Dict[str, Any]] = []
        for j in db_jobs:
            if hasattr(j, "__dict__"):
                job_dict = {k: v for k, v in j.__dict__.items() if not k.startswith("_")}
            elif isinstance(j, dict):
                job_dict = j
            else:
                job_dict = {}
            jobs.append(job_dict)

        # 3. الفلاتر الإضافية (Salary / Score)
        if company:
            jobs = [
                j for j in jobs
                if company.lower() in str(j.get("company", "")).lower()
            ]

        if location:
            jobs = [
                j for j in jobs
                if location.lower() in str(j.get("location", "")).lower()
            ]

        if salary_min is not None:
            jobs = [
                j for j in jobs
                if (j.get("salary") or 0) >= salary_min
            ]

        if salary_max is not None:
            jobs = [
                j for j in jobs
                if (j.get("salary") or 0) <= salary_max
            ]

        if score_min is not None:
            jobs = [
                j for j in jobs
                if (j.get("score") or 0) >= score_min
            ]

        if score_max is not None:
            jobs = [
                j for j in jobs
                if (j.get("score") or 0) <= score_max
            ]

        # 4. الترتيب (Sorting)
        allowed = {
            "score",
            "salary",
            "title",
            "provider",
            "location",
        }
        if sort in allowed:
            jobs.sort(
                key=lambda x: x.get(sort) or 0 if isinstance(x.get(sort), (int, float)) else str(x.get(sort) or "").lower(),
                reverse=(order == "desc"),
            )

        # 5. الترقيم (Pagination)
        total = db_total if db_total > 0 else len(jobs)
        start = (page - 1) * limit
        end = start + limit
        paged_jobs = jobs[start:end] if len(jobs) > limit else jobs

        return {
            "jobs": paged_jobs,
            "total": total,
            "page": page,
            "limit": limit,
        }
