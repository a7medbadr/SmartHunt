import asyncio
import logging
from typing import List, Optional
from smarthunt.browser.registry import ProviderRegistry
from smarthunt.database.models.job import Job

logger = logging.getLogger(__name__)


class ProviderManager:
    def __init__(self, registry: Optional[ProviderRegistry] = None):
        self.registry = registry or ProviderRegistry()

    async def search_all(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Job]:
        # التوافق مع Property أو Method
        providers_attr = getattr(self.registry, "providers", [])
        providers = providers_attr() if callable(providers_attr) else providers_attr

        if not providers:
            logger.info("No providers found in registry.")
            return []

        tasks = [
            provider.search(
                query=query,
                location=location,
            )
            for provider in providers
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        all_jobs: List[Job] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Provider search raised exception: {result}")
                continue
            if isinstance(result, list):
                all_jobs.extend(result)

        return all_jobs
