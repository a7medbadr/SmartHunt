from smarthunt.browser.providers.base import JobProvider
from smarthunt.domain import DiscoveredJob


class ExampleProvider(JobProvider):
    name: str = "example"

    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[DiscoveredJob]:

        return [
            DiscoveredJob(
                title=f"Senior {keyword} Developer",
                company="Example Corp",
                location=location or "Remote",
                source="Example",
                url="https://example.com/job/1",
            )
        ]
