from __future__ import annotations
from abc import ABC
from abc import abstractmethod

class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def search(
        self,
        query: str | None,
        location: str | None,
        page: int,
        limit: int,
    ):
        raise NotImplementedError
