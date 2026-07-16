from smarthunt.providers.base.provider import JobProvider
from smarthunt.providers.models.job import Job

class LinkedInProvider(JobProvider):
    name = "linkedin"

    async def search(self, keyword: str, location: str | None = None) -> list[Job]:
        if keyword and keyword.lower() != "linux":
            return []
        return [
            Job(
                external_id="ln-1",
                provider=self.name,
                title="Senior Linux System Administrator",
                company="SmartHunt Corp",
                location="Riyadh",
                url="https://linkedin.com/jobs/1",
                description="Looking for an expert Senior Linux System Administrator with deep RHEL and infrastructure automation skills.",
                salary="15000",
                remote=False,
                country="Saudi Arabia",
                city="Riyadh"
            )
        ]
