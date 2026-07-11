from smarthunt.browser.registry import ProviderRegistry


class ScraperService:

    def __init__(self):

        self.registry = ProviderRegistry()

    async def discover(
        self,
        keyword: str,
        location: str | None = None,
    ):

        jobs = []

        for provider in self.registry.get_all():

            result = await provider.search(
                keyword=keyword,
                location=location,
            )

            jobs.extend(result)

        return jobs
