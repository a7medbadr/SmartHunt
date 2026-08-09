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
        providers: list[str] | None = None,
    ) -> dict:
        """`providers`, when given, restricts the fan-out to just those
        provider names (still intersected with enabled/disabled — a
        disabled provider stays unsearchable even if explicitly named
        here) — added 2026-08-07 for discover_tanqeeb_daily's dedicated
        sweep, which needs the exact same filtered/scored/saved pipeline
        every other scheduled discovery job goes through (Saudi-location
        filter, title-relevance filter, scheduler_history tracking), just
        restricted to one named provider instead of every enabled one.
        Omitting it (the default) keeps the existing "every enabled
        provider" behavior every other caller already relies on."""

        enabled_map = await provider_settings_service.get_enabled_map(self.session)
        active_providers = [
            p for p in provider_registry.providers() if enabled_map.get(p.name, True)
        ]
        if providers is not None:
            wanted = {p.lower() for p in providers}
            active_providers = [p for p in active_providers if p.name.lower() in wanted]

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
            # A job explicitly marked "Remote" (e.g. baaeed's listings) is
            # still a real option for the owner regardless of the physical
            # location searched for, so it always passes this filter rather
            # than being silently excluded from every Saudi-only scheduled
            # run — found 2026-08-03 while investigating why baaeed had
            # produced zero jobs despite real_discovery=True.
            needle = location.lower()
            jobs = [
                j
                for j in jobs
                if needle in (j.location or "").lower() or "remote" in (j.location or "").lower()
            ]

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
            "providers": len(active_providers),
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

    async def search_single_provider(
        self,
        provider_name: str,
        query: str,
        location: str | None = None,
        limit: int = 25,
    ) -> dict:
        """Live-searches exactly one named provider's own site and saves
        whatever it returns — the "search this specific site" feature
        (2026-08-04). Still respects the enabled/disabled provider
        setting — a disabled provider stays genuinely unsearchable
        everywhere, not just hidden from the automated pipeline.

        Applies the same strict title-relevance filter as discover()
        (see its own comment above for why a query match alone isn't a
        relevance signal) — found live 2026-08-04: an early version of
        this method skipped it on the theory that "the owner picked this
        site/query deliberately, they should see the raw results," but
        LinkedIn's own broadened search results (QA testers, product
        managers, etc. for a "Linux Administrator" query) landed in the
        *same* shared jobs list the owner browses generally, with
        misleadingly high scores from the ratio-based matcher on a small
        skill set — exactly the "jobs with no relation to my work"
        clutter the owner explicitly asked to have removed. Deliberately
        does NOT force the Saudi-only location filter, though — the
        owner typed a specific location (or none) for this specific
        search and that should be respected as-is, unlike the scheduled
        pipeline's fixed scope."""

        target = next(
            (p for p in provider_registry.providers() if p.name == provider_name),
            None,
        )
        if target is None:
            raise ValueError(f"Unknown provider: {provider_name!r}")

        enabled_map = await provider_settings_service.get_enabled_map(self.session)
        if not enabled_map.get(provider_name, True):
            raise ValueError(f"Provider {provider_name!r} is disabled")

        jobs = await provider_registry.fetch_all_jobs(
            query=query,
            location=location,
            limit=limit,
            providers=[target],
        )

        jobs = [j for j in jobs if is_relevant_job_title(j.title)]

        inserted = await self.repository.save_discovered_jobs(jobs)

        result = {
            "provider": provider_name,
            "found": len(jobs),
            "inserted": inserted,
            "duplicates": len(jobs) - inserted,
        }

        await scheduler_history_service.create(
            self.session,
            SchedulerHistoryCreate(
                provider=f"site-search:{provider_name}",
                status="completed",
                jobs_found=len(jobs),
                message=f"query={query!r} location={location!r} inserted={inserted}",
            ),
        )

        return result
