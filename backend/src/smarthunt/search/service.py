from __future__ import annotations

from typing import Any

from smarthunt.database import session as db_session
from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.providers.registry.registry import ProviderRegistry
from smarthunt.providers.health.monitor import monitor
from smarthunt.search.cache import cache
from smarthunt.search.metrics import metrics


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

        key = f"{query}:{location}:{provider}:{page}:{limit}"

        cached = cache.get(key)
        if cached:
            metrics.search(results_count=len(cached.get("jobs", [])))
            metrics.cache_hit()
            return cached

        metrics.provider_call()
        jobs: list[dict] = []

        providers = self.registry.providers()

        for item in providers:
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

                if isinstance(result, dict):
                    provider_jobs = result.get("results") or []
                elif isinstance(result, list):
                    provider_jobs = result
                else:
                    provider_jobs = []

                for job in provider_jobs:
                    job.setdefault("provider", provider_name)

                jobs.extend(provider_jobs)
                self.monitor.success(provider_name)

            except Exception:
                self.monitor.failure(provider_name)

        # Distinct
        unique = {}
        for job in jobs:
            key_item = (
                job.get("provider"),
                job.get("title"),
                job.get("location"),
            )
            unique[key_item] = job

        jobs = list(unique.values())
        jobs.sort(key=lambda x: x.get("score", 0), reverse=True)

        start = (page - 1) * limit
        end = start + limit
        paged = jobs[start:end]

        if paged and db_session.AsyncSessionLocal:
            async with db_session.AsyncSessionLocal() as session:
                repo = JobRepository(session)
                await repo.save_many(paged)

        response_data = {
            "jobs": paged,
            "total": len(jobs),
            "page": page,
            "limit": limit,
        }

        metrics.search(results_count=len(paged))
        cache.set(key, response_data)

        return response_data
