from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job


class LinkedInProvider(BaseProvider):

    name = "linkedin"

    supports_login = True
    supports_apply = True
    supports_resume_upload = True
    supports_cover_letter = True

    async def search(
        self,
        query=None,
        location=None,
        page=1,
        limit=25,
    ) -> list[Job]:

        return [
            Job(
                external_id="linkedin-1",
                provider=self.name,
                title="Senior Linux Engineer",
                company="LinkedIn Demo",
                location=location or "Remote",
                url="https://linkedin.com/job/1",
                description="Linux OpenShift Kubernetes",
                salary="18000",
                remote=True,
                city="Riyadh",
                country="Saudi Arabia",
            )
        ]
