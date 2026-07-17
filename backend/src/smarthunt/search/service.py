from __future__ import annotations

from typing import Any

from smarthunt.database import session as db_session
from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.providers.registry.registry import ProviderRegistry
from smarthunt.providers.health.monitor import monitor


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
                )

                if result:
                    jobs.extend(result)

                self.monitor.success(provider_name)

            except Exception:
                self.monitor.failure(provider_name)

        # Remove duplicates
        unique = {}
        for job in jobs:
            key = (
                job.get("provider"),
                job.get("title"),
                job.get("location"),
            )
            unique[key] = job

        jobs = list(unique.values())

        jobs.sort(
            key=lambda x: x.get("score", 0),
            reverse=True,
        )

        start = (page - 1) * limit
        end = start + limit

        paged = jobs[start:end]

        if paged and db_session.AsyncSessionLocal:

            async with db_session.AsyncSessionLocal() as session:

                repo = JobRepository(session)

                await repo.save_many(paged)

        return {
            "jobs": paged,
            "total": len(jobs),
            "page": page,
            "limit": limit,
        }
