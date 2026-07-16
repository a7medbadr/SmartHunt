from smarthunt.providers.base.provider import JobProvider
from smarthunt.providers.models.job import Job

class WuzzufProvider(JobProvider):
    name = "wuzzuf"

    async def search(self, keyword: str, location: str | None = None) -> list[Job]:
        return []
