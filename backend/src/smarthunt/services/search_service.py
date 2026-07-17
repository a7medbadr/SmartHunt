import logging
from typing import Optional, List, Dict, Any
from types import SimpleNamespace
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.providers.manager import ProviderManager

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(
        self,
        session: Optional[AsyncSession] = None,
        provider_manager: Optional[ProviderManager] = None
    ):
        self.session = session
        self.job_repo = JobRepository(session) if session else JobRepository()
        self.provider_manager = provider_manager or ProviderManager()

    async def search(
        self,
        query: Optional[str] = None,
        company: Optional[str] = None,
        location: Optional[str] = None,
        provider: Optional[str] = None,
        salary_min: Optional[int] = None,
        salary_max: Optional[int] = None,
        score_min: Optional[int] = None,
        score_max: Optional[int] = None,
        sort: str = "score",
        order: str = "desc",
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:

        # 1. إعداد الـ params للتوافق مع DB Repository
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

        # 2. جلب الوظائف المحفوظة في قاعدة البيانات
        db_jobs, db_total = await self.job_repo.search_jobs(params)

        # 3. استدعاء الـ Providers في الخلفية إذا طُلب ذلك أو لدمج النتائج
        live_jobs = []
        if self.provider_manager.providers:
            live_jobs = await self.provider_manager.search_all(
                query=query,
                location=location,
                provider_name=provider
            )

        # 4. تجميع وتحويل الكائنات إلى Dicts
        jobs: List[Dict[str, Any]] = []

        # إضافة نتائج قاعدة البيانات
        for j in db_jobs:
            if hasattr(j, "__dict__"):
                job_dict = {k: v for k, v in j.__dict__.items() if not k.startswith("_")}
            elif isinstance(j, dict):
                job_dict = j
            else:
                job_dict = {}
            jobs.append(job_dict)

        # إضافة نتائج الـ Live Providers إن وجدت مع تجنب التكرار
        existing_urls = {j.get("url") for j in jobs if j.get("url")}
        for lj in live_jobs:
            lj_url = getattr(lj, "url", None) or (lj.get("url") if isinstance(lj, dict) else None)
            if lj_url and lj_url in existing_urls:
                continue

            if hasattr(lj, "__dict__"):
                lj_dict = {k: v for k, v in lj.__dict__.items() if not k.startswith("_")}
            elif isinstance(lj, dict):
                lj_dict = lj
            else:
                lj_dict = {}

            jobs.append(lj_dict)

        # 5. التصفية الإضافية (Company, Salary, Score)
        if company:
            jobs = [j for j in jobs if company.lower() in str(j.get("company", "")).lower()]

        if location:
            jobs = [j for j in jobs if location.lower() in str(j.get("location", "")).lower()]

        if salary_min is not None:
            jobs = [j for j in jobs if (j.get("salary") or 0) >= salary_min]

        if salary_max is not None:
            jobs = [j for j in jobs if (j.get("salary") or 0) <= salary_max]

        if score_min is not None:
            jobs = [j for j in jobs if (j.get("score") or 0) >= score_min]

        if score_max is not None:
            jobs = [j for j in jobs if (j.get("score") or 0) <= score_max]

        # 6. الترتيب (Sorting)
        allowed_sorts = {"score", "salary", "title", "provider", "location"}
        if sort in allowed_sorts:
            jobs.sort(
                key=lambda x: x.get(sort) or 0 if isinstance(x.get(sort), (int, float)) else str(x.get(sort) or "").lower(),
                reverse=(order == "desc"),
            )

        # 7. الترقيم (Pagination)
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
