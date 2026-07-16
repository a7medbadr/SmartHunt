from __future__ import annotations
from typing import Any
import sys
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
                # التأكد الصارم أن النتيجة عبارة عن قائمة (List)
                if result and isinstance(result, list):
                    for job in result:
                        # والتأكد أن كل وظيفة عبارة عن Dictionary وليس String أو أي شيء آخر
                        if isinstance(job, dict):
                            jobs.extend([job])
                        else:
                            print(f"--> [WARNING] Provider {p.name} returned a non-dict item: {type(job)}", file=sys.stderr, flush=True)
            except BaseException as e:
                print(f"--> [DEBUG] Provider {p.name} failed with error: {str(e)}", file=sys.stderr, flush=True)
                continue

        # الترتيب بأمان الآن بعد ضمان أن كل العناصر قواميس ولديها دالة get
        jobs.sort(
            key=lambda x: x.get("score", 0) if isinstance(x, dict) else 0,
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
