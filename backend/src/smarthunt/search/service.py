from __future__ import annotations
from typing import Any

from smarthunt.providers.registry.registry import ProviderRegistry
from smarthunt.providers.health.monitor import monitor
from smarthunt.database import session as db_session
from smarthunt.database.repositories.job_repository import JobRepository

class SearchService:
    def __init__(self) -> None:
        self.registry = ProviderRegistry()
        self.monitor = monitor

    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        provider: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> dict[str, Any]:
        
        # 1. شغل كود البحث الأصلي
        jobs = []
        # providers = self.registry.providers()
        
        # 2. حفظ الـ jobs الناتجة جوه الـ Database باستخدام الـ Factory المتاح
        if jobs and db_session.AsyncSessionLocal:
            async with db_session.AsyncSessionLocal() as session:
                repo = JobRepository(session)
                await repo.save_many(jobs)

        return {
            "jobs": jobs,
            "total": len(jobs),
            "page": page,
            "limit": limit
        }
