from typing import Any, Dict
from types import SimpleNamespace
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.repositories.job_repository import JobRepository


class SearchService:
    def __init__(self, session: AsyncSession):
        self.repository = JobRepository(session)

    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        provider: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:
        params = SimpleNamespace(
            title=query,
            company=None,
            location=location,
            provider=provider,
            sort="created_at",
            order="desc",
            page=page,
            limit=limit,
        )
        jobs, total = await self.repository.search_jobs(params)
        
        return {
            "items": jobs,
            "total": total,
            "page": page,
            "limit": limit,
        }
