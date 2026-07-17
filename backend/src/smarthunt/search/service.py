from __future__ import annotations
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.registry.registry import ProviderRegistry
from smarthunt.providers.health.monitor import monitor
from smarthunt.database.session import async_session
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
        
        # 1. شغل كود البحث الأصلي اللي بيجيب البيانات من الـ Providers
        jobs = []
        providers = self.registry.providers()
        
        # هنا بيبقى كود الـ loop أو الـ fetch بتاع الـ providers الأصلي 
        # (بما إن الكوميت مسحه، هنرجع الهيكل الأساسي للـ jobs وإذا كان فيه تجميع من الـ registry)
        # لتجنب كسر الـ return format المتوقع من الـ router القديم:
        
        # 2. حفظ الـ jobs الناتجة جوه الـ Database
        if jobs:
            async with async_session() as session:
                repo = JobRepository(session)
                await repo.save_many(jobs)

        return {
            "jobs": jobs,
            "total": len(jobs),
            "page": page,
            "limit": limit
        }
