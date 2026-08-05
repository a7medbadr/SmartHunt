from __future__ import annotations

import asyncio
from dataclasses import asdict, is_dataclass

from smarthunt.domain.job import DiscoveredJob
from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.baaeed.provider import BaaeedProvider
from smarthunt.providers.bayt.provider import BaytProvider
from smarthunt.providers.drjobs.provider import DrjobsProvider
from smarthunt.providers.forasnagulf.provider import ForasnagulfProvider
from smarthunt.providers.gulftalent.provider import GulfTalentProvider
from smarthunt.providers.indeed.provider import IndeedProvider
from smarthunt.providers.linkedin.provider import LinkedInProvider
from smarthunt.providers.monstergulf.provider import MonstergulfProvider
from smarthunt.providers.naukrigulf.provider import NaukrigulfProvider
from smarthunt.providers.sabbar.provider import SabbarProvider
from smarthunt.providers.tanqeeb.provider import TanqeebProvider
from smarthunt.providers.wuzzuf.provider import WuzzufProvider
from smarthunt.providers.wzayef.provider import WzayefProvider


class ProviderRegistry:

    def providers(self) -> list[BaseProvider]:
        return [
            LinkedInProvider(),
            IndeedProvider(),
            GulfTalentProvider(),
            BaytProvider(),
            WuzzufProvider(),
            NaukrigulfProvider(),
            MonstergulfProvider(),
            WzayefProvider(),
            TanqeebProvider(),
            DrjobsProvider(),
            ForasnagulfProvider(),
            SabbarProvider(),
            BaaeedProvider(),
        ]

    def _normalize(self, item) -> DiscoveredJob:

        if isinstance(item, DiscoveredJob):
            return item

        if hasattr(item, "to_domain"):
            return item.to_domain()

        if is_dataclass(item):
            item = asdict(item)

        if isinstance(item, dict):
            return DiscoveredJob(
                title=item.get("title", ""),
                company=item.get("company", ""),
                location=item.get("location", ""),
                source=item.get(
                    "source",
                    item.get("provider", ""),
                ),
                url=item.get("url") or None,
                description=item.get("description", ""),
                requirements=item.get("requirements", ""),
            )

        raise TypeError(f"Unsupported provider object: {type(item)}")

    async def fetch_all_jobs(
        self,
        query: str | None = None,
        location: str | None = None,
        page: int = 1,
        limit: int = 25,
        providers: list[BaseProvider] | None = None,
    ) -> list[DiscoveredJob]:

        tasks = [
            provider.search(
                query=query,
                location=location,
                page=page,
                limit=limit,
            )
            for provider in (providers if providers is not None else self.providers())
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        jobs: list[DiscoveredJob] = []

        for result in results:

            if isinstance(result, Exception):
                continue

            for job in result:
                jobs.append(self._normalize(job))

        return jobs


provider_registry = ProviderRegistry()
