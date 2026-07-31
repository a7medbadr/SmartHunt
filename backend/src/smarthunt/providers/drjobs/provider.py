from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job


class DrjobsProvider(BaseProvider):

    name = "drjobs"

    async def search(
        self,
        query=None,
        location=None,
        page=1,
        limit=25,
    ) -> list[Job]:

        return [
            Job(
                external_id="drjobs-1",
                provider=self.name,
                title="Platform Engineer",
                company="DrJobs Demo",
                location=location or "Remote",
                url="https://drjobs.com/job/1",
                description="Platform Engineering OpenShift",
                salary="17500",
                remote=False,
                city="Riyadh",
                country="Saudi Arabia",
            )
        ]
