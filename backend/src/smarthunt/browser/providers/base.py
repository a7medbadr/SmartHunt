from abc import ABC, abstractmethod

from smarthunt.browser.base import JobResult


class JobProvider(ABC):
    name: str

    @abstractmethod
    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[JobResult]:
        raise NotImplementedError
