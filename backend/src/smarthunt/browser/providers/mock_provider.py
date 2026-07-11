from smarthunt.browser.base import JobResult
from smarthunt.browser.providers.base import JobProvider


class MockProvider(JobProvider):
    name = "Mock"

    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[JobResult]:
        return [
            JobResult(
                title=f"{keyword} Engineer",
                company="OpenAI",
                location=location or "Remote",
                source=self.name,
                url="https://example.com/jobs/mock-1",
            ),
            JobResult(
                title=f"Senior {keyword}",
                company="Red Hat",
                location=location or "Riyadh",
                source=self.name,
                url="https://example.com/jobs/mock-2",
            ),
        ]
