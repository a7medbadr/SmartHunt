import asyncio
import logging
import time
from typing import List, Optional
from smarthunt.database.models.job import Job
from smarthunt.providers.interfaces import BaseProvider

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Manages job search providers, running them concurrently with timeouts and isolation.
    """

    def __init__(
        self,
        providers: Optional[List[BaseProvider]] = None,
        timeout: float = 10.0
    ):
        self.providers: List[BaseProvider] = providers or []
        self.timeout = timeout

    def register_provider(self, provider: BaseProvider) -> None:
        self.providers.append(provider)

    async def search_all(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> List[Job]:
        active_providers = self.providers

        # Filter by provider name if specified
        if provider_name:
            active_providers = [
                p for p in self.providers
                if getattr(p, "name", "").lower() == provider_name.lower()
            ]
            if not active_providers:
                logger.warning(f"No registered provider matched name: {provider_name}")
                return []

        if not active_providers:
            logger.info("No active providers registered for search.")
            return []

        # Run all provider searches concurrently
        tasks = [
            self._search_single_provider(provider, query, location)
            for provider in active_providers
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_jobs: List[Job] = []
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Provider failed with unhandled exception: {result}")

        return all_jobs

    async def _search_single_provider(
        self,
        provider: BaseProvider,
        query: Optional[str],
        location: Optional[str]
    ) -> List[Job]:
        p_name = getattr(provider, "name", provider.__class__.__name__)
        logger.info(f"Searching {p_name}...")
        start_time = time.perf_counter()

        try:
            jobs = await asyncio.wait_for(
                provider.search(query=query, location=location),
                timeout=self.timeout
            )
            elapsed = time.perf_counter() - start_time
            logger.info(f"{p_name} finished ({elapsed:.2f} sec) - Found {len(jobs)} jobs")
            return jobs
        except asyncio.TimeoutError:
            logger.warning(f"{p_name} timeout after {self.timeout}s")
            return []
        except Exception as exc:
            logger.warning(f"{p_name} failed with error: {exc}")
            return []
