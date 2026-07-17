from typing import List, Optional, Protocol, runtime_checkable
from smarthunt.database.models.job import Job


@runtime_checkable
class BaseProvider(Protocol):
    """
    Standard interface that all real and mock providers must implement.
    """

    name: str

    async def search(
        self,
        query: Optional[str] = None,
        location: Optional[str] = None,
    ) -> List[Job]:
        ...

    async def health(self) -> bool:
        ...

    async def login(self) -> bool:
        ...
