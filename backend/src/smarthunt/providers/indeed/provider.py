from smarthunt.providers.base.provider import JobProvider
from smarthunt.providers.models.job import Job

class IndeedProvider(JobProvider):
    name = "indeed"

    async def search(self, keyword: str, location: str | None = None) -> list[Job]:
        return [
            Job(
                external_id="id-1",
                provider=self.name,
                title="DevOps Engineer",
                company="LinkedIn Inc",
                location="Remote",
                url="https://indeed.com/jobs/2",
                description="Seeking a Mid-level DevOps Engineer experienced in Kubernetes, Linux systems administration, and Cl/CD.",
                salary="12000",
                remote=True,
                country="US",
                city="Remote"
            )
        ]
