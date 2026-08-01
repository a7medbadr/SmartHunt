from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.registry import provider_registry
from smarthunt.providers.settings.service import provider_settings_service
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

        enabled_map = await provider_settings_service.get_enabled_map(self.session)
        active_providers = [
            p for p in provider_registry.providers() if enabled_map.get(p.name, True)
        ]

        jobs = await provider_registry.fetch_all_jobs(
            query=query,
            location=location,
            page=page,
            limit=limit,
            providers=active_providers,
        )

        if location:
            # Providers are asked for `location`, but that's a search hint,
            # not a guarantee — don't trust a provider to actually honor it.
            needle = location.lower()
            jobs = [j for j in jobs if needle in (j.location or "").lower()]

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
