from smarthunt.providers.base.provider import BaseProvider
from typing import Any


class BaytProvider(BaseProvider):
    name = "bayt"
    supports_login = True
    supports_apply = True
    supports_resume_upload = True
    supports_cover_letter = True

    async def search(
        self,
        query: str | None,
        location: str | None,
        page: int,
        limit: int,
    ) -> Any:
        return {"provider": self.name, "results": [], "page": page, "limit": limit}
