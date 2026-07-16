from smarthunt.providers.base.provider import BaseProvider
from typing import Any

class IndeedProvider(BaseProvider):
    name = "indeed"
    supports_login = False
    supports_apply = False
    supports_resume_upload = False
    supports_cover_letter = False

    async def search(
        self,
        query: str | None,
        location: str | None,
        page: int,
        limit: int,
    ) -> Any:
        return {"provider": self.name, "results": [], "page": page, "limit": limit}
