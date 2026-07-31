from __future__ import annotations

from abc import ABC, abstractmethod

from smarthunt.domain.job import DiscoveredJob


class BaseProvider(ABC):
    """
    Base interface implemented by every production provider.
    """

    name: str = ""

    supports_login: bool = False
    supports_apply: bool = False
    supports_resume_upload: bool = False
    supports_cover_letter: bool = False

    @abstractmethod
    async def search(
        self,
        query: str | None = None,
        location: str | None = None,
        page: int = 1,
        limit: int = 25,
    ) -> list[DiscoveredJob]:
        """
        Return normalized discovered jobs.
        """
        raise NotImplementedError
