from __future__ import annotations

from typing import Protocol

from smarthunt.domain.job import DiscoveredJob


class ProviderProtocol(Protocol):

    name: str

    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> list[DiscoveredJob]:
        ...

    async def login(self) -> bool:
        ...

    async def health(self) -> bool:
        ...
