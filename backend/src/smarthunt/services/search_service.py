from typing import Any, Dict
from types import SimpleNamespace
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.database.repositories.search_history_repository import SearchHistoryRepository


class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = JobRepository(session)
        self.history_repo = SearchHistoryRepository(session)

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

        # Record search history in DB
        await self.history_repo.create(
            query=query,
            provider=provider,
            location=location,
            results_count=total,
        )

        return {
            "items": jobs,
            "total": total,
            "page": page,
            "limit": limit,
        }

    async def get_history(self, limit: int = 10) -> Dict[str, Any]:
        items = await self.history_repo.list_recent(limit=limit)
        return {
            "count": len(items),
            "items": [
                {
                    "query": h.query,
                    "provider": h.provider,
                    "location": h.location,
                    "results": h.results_count,
                    "created_at": h.created_at.isoformat() if h.created_at else None,
                }
                for h in items
            ],
        }

    async def clear_history(self) -> Dict[str, str]:
        await self.history_repo.delete_all()
        return {"status": "success", "message": "Search history cleared successfully"}
