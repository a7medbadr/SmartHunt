from smarthunt.providers import registry

class SearchService:
    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ):
        jobs = []
        for provider in registry.all():
            jobs.extend(
                await provider.search(
                    keyword=keyword,
                    location=location,
                )
            )
        return jobs

search_service = SearchService()
