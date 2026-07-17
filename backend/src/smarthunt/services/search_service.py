from types import SimpleNamespace
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.database.repositories.search_history_repository import SearchHistoryRepository
from smarthunt.providers.registry import ProviderRegistry
from smarthunt.providers.health.monitor import monitor


class SearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = JobRepository(session)
        self.history_repo = SearchHistoryRepository(session)
        self.registry = ProviderRegistry()
        self.monitor = monitor

    async def _fetch_from_providers(
        self,
        query: str | None,
        location: str | None,
        provider: str | None,
        page: int,
        limit: int,
    ) -> list[dict]:
        """Calls every registered provider, normalizes their response shape,
        and returns a flat list of job dicts. Never raises — failures are
        recorded in the health monitor instead."""
        collected: list[dict] = []

        for item in self.registry.providers():
            provider_name = item.name.lower()

            if provider and provider_name != provider.lower():
                continue

            try:
                result = await item.search(
                    query=query,
                    location=location,
                    page=page,
                    limit=limit,
                )

                # Providers currently return one of two shapes:
                #   - a dict: {"provider": ..., "results": [...], ...}
                #   - a bare list: [{...}, {...}]
                if isinstance(result, dict):
                    provider_jobs = result.get("results") or []
                elif isinstance(result, list):
                    provider_jobs = result
                else:
                    provider_jobs = []

                for job in provider_jobs:
                    job.setdefault("provider", provider_name)

                collected.extend(provider_jobs)
                self.monitor.success(provider_name)

            except Exception:
                self.monitor.failure(provider_name)

        return collected

    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        provider: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> Dict[str, Any]:

        # 1. Pull fresh results from providers and persist any new ones
        fresh_jobs = await self._fetch_from_providers(
            query=query,
            location=location,
            provider=provider,
            page=page,
            limit=limit,
        )
        if fresh_jobs:
            await self.repository.save_many(fresh_jobs)

        # 2. Serve the paginated result set from the database
        #    (single source of truth after providers have written into it)
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

        # 3. Record search history
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
