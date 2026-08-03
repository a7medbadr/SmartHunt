from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.registry import provider_registry
from smarthunt.providers.settings.service import provider_settings_service
from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.matching.services.job_relevance import is_relevant_job_title
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

        # Providers' own search (LinkedIn's especially) semantically
        # broadens a query like "Linux Administrator" far past the
        # owner's actual, narrow skill set — Systems Engineer, Network
        # Security Engineer, SAP consultant, fire-alarm systems, DB
        # administrator, anything Manager/Architect-level, and postings
        # restricted to Saudi nationals (the owner is an iqama holder,
        # not a Saudi national, and can't apply to those at all) have
        # all shown up from a query match alone. A query match is not a
        # relevance signal; the title itself must be.
        jobs = [j for j in jobs if is_relevant_job_title(j.title)]

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
