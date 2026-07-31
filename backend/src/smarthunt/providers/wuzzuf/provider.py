from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job


class WuzzufProvider(BaseProvider):
    name = "wuzzuf"
    supports_login = True
    supports_apply = True
    supports_resume_upload = True
    supports_cover_letter = False

    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> list[Job]:
        return []
