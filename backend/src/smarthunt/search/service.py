from smarthunt.providers import registry
from smarthunt.search.deduplication import DeduplicationEngine
from smarthunt.search.ranking import RankingEngine
from smarthunt.search.models import SearchJobItem, SearchResult

class SearchService:
    async def search_jobs(
        self,
        title: str | None,
        location: str | None,
        provider: str | None,
        page: int,
        limit: int,
    ) -> SearchResult:
        providers = registry.all()
        if provider:
            providers = [p for p in providers if p.name == provider]

        raw_jobs = []
        for p in providers:
            raw_jobs.extend(
                await p.search(
                    keyword=title or "",
                    location=location,
                )
            )

        unique_jobs = DeduplicationEngine.deduplicate(raw_jobs)
        ranked_jobs = RankingEngine.rank_jobs(unique_jobs)

        mapped_items = []
        for idx, (job, score, details) in enumerate(ranked_jobs, start=1):
            try:
                sal_val = int(job.salary) if job.salary else None
            except ValueError:
                sal_val = None

            mapped_items.append(
                SearchJobItem(
                    id=idx,
                    title=job.title,
                    location=job.location,
                    provider=job.provider,
                    salary=sal_val,
                    experience="senior" if "senior" in job.title.lower() else "mid",
                    remote=job.remote,
                    onsite=not job.remote,
                    hybrid=False,
                    country=job.country,
                    city=job.city,
                    score=score,
                    match_details=details
                )
            )

        if location:
            mapped_items = [item for item in mapped_items if location.lower() in item.location.lower()]

        total = len(mapped_items)
        start = (page - 1) * limit
        end = start + limit
        items = mapped_items[start:end]

        return SearchResult(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

search_service = SearchService()
