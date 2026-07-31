from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job


class GulfTalentProvider(BaseProvider):
    name = "gulftalent"
    supports_login = True
    supports_apply = True
    supports_resume_upload = True
    supports_cover_letter = True

    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> list[Job]:
        return []
