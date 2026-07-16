from smarthunt.providers.base.provider import JobProvider
from smarthunt.providers.models.job import Job

class GulfTalentProvider(JobProvider):
    name = "gulftalent"

    async def search(self, keyword: str, location: str | None = None) -> list[Job]:
        return [
            Job(
                external_id="gt-1",
                provider=self.name,
                title="Infrastructure Engineer",
                company="GulfTalent Ltd",
                location="Riyadh",
                url="https://gulftalent.com/jobs/3",
                description="We need an Infrastructure Engineer proficient in UNIX/Linux administration, IBM AIX, and OpenShift architecture.",
                salary="14000",
                remote=False,
                country="Saudi Arabia",
                city="Riyadh"
            )
        ]
