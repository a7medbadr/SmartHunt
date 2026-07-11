from smarthunt.browser.providers import MockProvider


class ScraperService:
    def __init__(self):
        self.providers = [
            MockProvider(),
        ]

    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ):
        jobs = []

        for provider in self.providers:
            jobs.extend(
                await provider.search(
                    keyword=keyword,
                    location=location,
                )
            )

        return jobs
