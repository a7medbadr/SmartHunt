from smarthunt.browser.providers.base import JobProvider
from smarthunt.domain import DiscoveredJob


class MockProvider2(JobProvider):
    name: str = "mock2"

    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[DiscoveredJob]:

        return [
            DiscoveredJob(
                title=f"Lead {keyword}",
                company="Microsoft",
                location=location or "Remote",
                source="Mock2",
                url="https://example.com/mock2/job1",
            ),
            DiscoveredJob(
                title=f"Principal {keyword}",
                company="Amazon",
                location=location or "Dubai",
                source="Mock2",
                url="https://example.com/mock2/job2",
            ),
        ]
