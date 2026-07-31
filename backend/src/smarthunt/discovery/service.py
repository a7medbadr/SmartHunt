from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.registry import provider_registry
from smarthunt.database.repositories.job_repository import JobRepository


class DiscoveryService:

    def __init__(self, session: AsyncSession):
        self.repository = JobRepository(session)

    async def discover(
        self,
        query: str,
        location: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> dict:

        jobs = await provider_registry.fetch_all_jobs(
            query=query,
            location=location,
            page=page,
            limit=limit,
        )

        inserted = await self.repository.save_discovered_jobs(
            jobs
        )

        return {
            "providers": len(provider_registry.providers()),
            "discovered": len(jobs),
            "inserted": inserted,
            "duplicates": len(jobs) - inserted,
        }
