from smarthunt.browser.base import JobResult
from smarthunt.browser.providers.base import JobProvider


class ExampleProvider(JobProvider):
    name: str = "example"

    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[JobResult]:

        return [
            JobResult(
                title=f"Senior {keyword} Developer",
                company="Example Corp",
                location=location or "Remote",
                source="Example",
                url="https://example.com/job/1",
            )
        ]
