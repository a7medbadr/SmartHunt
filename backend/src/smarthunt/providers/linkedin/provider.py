from smarthunt.providers.base.provider import JobProvider
from smarthunt.providers.models.job import Job

class LinkedInProvider(JobProvider):
    name = "linkedin"

    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[Job]:
        return [
            Job(
                external_id="ln-1",
                provider=self.name,
                title="Senior Linux Engineer",
                company="Demo Company",
                location="Riyadh",
                url="https://linkedin.com/jobs/demo",
                description="Demo Job",
                remote=False,
                country="Saudi Arabia",
                city="Riyadh",
            )
        ]
