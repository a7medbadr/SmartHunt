from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.registry import provider_registry
from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate
from smarthunt.scheduler.history.service import scheduler_history_service


class DiscoveryService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = JobRepository(session)

    async def discover(
        self,
        query: str,
        location: str | None = None,
        page: int = 1,
        limit: int = 25,
        provider: str = "manual-run",
    ) -> dict:

        jobs = await provider_registry.fetch_all_jobs(
            query=query,
            location=location,
            page=page,
            limit=limit,
        )

        inserted = await self.repository.save_discovered_jobs(jobs)

        result = {
            "providers": len(provider_registry.providers()),
            "discovered": len(jobs),
            "inserted": inserted,
            "duplicates": len(jobs) - inserted,
        }

        await scheduler_history_service.create(
            self.session,
            SchedulerHistoryCreate(
                provider=provider,
                status="completed",
                jobs_found=len(jobs),
                message=f"query={query!r} location={location!r} inserted={inserted}",
            ),
        )

        return result
