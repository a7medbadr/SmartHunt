from __future__ import annotations
from abc import ABC, abstractmethod
from smarthunt.providers.models.job import Job

class JobProvider(ABC):
    name: str

    @abstractmethod
    async def search(
        self,
        keyword: str,
        location: str | None = None,
    ) -> list[Job]:
        ...
