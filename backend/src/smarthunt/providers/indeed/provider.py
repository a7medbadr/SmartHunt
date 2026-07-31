from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job


class IndeedProvider(BaseProvider):

    name = "indeed"

    async def search(
        self,
        query=None,
        location=None,
    ) -> list[Job]:

        return [
            Job(
                external_id="indeed-1",
                provider=self.name,
                title="OpenShift Administrator",
                company="Indeed Demo",
                location=location or "Remote",
                url="https://indeed.com/job/1",
                description="OpenShift Kubernetes Linux",
                salary="16000",
                remote=False,
                city="Riyadh",
                country="Saudi Arabia",
            )
        ]
