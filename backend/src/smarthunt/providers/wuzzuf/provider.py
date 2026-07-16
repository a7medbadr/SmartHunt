from smarthunt.providers.base.provider import BaseProvider
from typing import Any

class WuzzufProvider(BaseProvider):
    name = "wuzzuf"
    supports_login = True
    supports_apply = True
    supports_resume_upload = True
    supports_cover_letter = False

    async def search(
        self,
        query: str | None,
        location: str | None,
        page: int,
        limit: int,
    ) -> Any:
        return {"provider": self.name, "results": [], "page": page, "limit": limit}
