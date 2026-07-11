from abc import ABC, abstractmethod

from smarthunt.domain import DiscoveredJob


class JobProvider(ABC):
    name: str

    @abstractmethod
    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[DiscoveredJob]:
        raise NotImplementedError
