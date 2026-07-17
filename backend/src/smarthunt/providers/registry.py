import asyncio
import logging
from typing import List, Dict, Any

logger = logging.getLogger("smarthunt.providers")


class ProviderRegistry:
    def __init__(self):
        self._providers = {}
        self._health_status = {}

    def register(self, name: str, provider_instance):
        self._providers[name] = provider_instance
        self._health_status[name] = {"healthy": True, "last_error": None}

    async def fetch_from_provider_safe(self, name: str, instance) -> List[Dict[str, Any]]:
        try:
            # Execute provider fetch
            if hasattr(instance, "fetch_jobs"):
                return await instance.fetch_jobs()
            return []
        except Exception as exc:
            logger.error(f"Provider '{name}' failed: {exc}. Marking unhealthy and returning empty gracefully.")
            self._health_status[name] = {"healthy": False, "last_error": str(exc)}
            return []

    async def fetch_all_jobs_safe(self) -> List[Dict[str, Any]]:
        tasks = [
            self.fetch_from_provider_safe(name, instance)
            for name, instance in self._providers.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_jobs = []
        for res in results:
            if isinstance(res, list):
                all_jobs.extend(res)
        return all_jobs

    def get_health_status(self) -> Dict[str, Any]:
        return self._health_status


provider_registry = ProviderRegistry()
