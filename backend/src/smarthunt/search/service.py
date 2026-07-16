from __future__ import annotations
from typing import Any
from smarthunt.providers.registry.registry import ProviderRegistry

class SearchService:
    def __init__(self) -> None:
        self.registry = ProviderRegistry()

    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        provider: str | None = None,
        page: int = 1,
        limit: int = 10,
    ) -> dict[str, Any]:

        jobs = []
        providers = self.registry.providers()

        if provider:
            providers = [
                p
                for p in providers
                if p.name.lower() == provider.lower()
            ]

        for p in providers:
            try:
                result = await p.search(
                    query=query,
                    location=location,
                    page=page,
                    limit=limit,
                )
                jobs.extend(result)
            except Exception:
                continue

        jobs.sort(
            key=lambda x: x.get("score", 0),
            reverse=True,
        )

        total = len(jobs)
        start = (page - 1) * limit
        end = start + limit

        return {
            "items": jobs[start:end],
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
        }
