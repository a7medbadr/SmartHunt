from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any

class BaseProvider(ABC):
    name: str = ""
    supports_login: bool = False
    supports_apply: bool = False
    supports_resume_upload: bool = False
    supports_cover_letter: bool = False

    @abstractmethod
    async def search(
        self,
        query: str | None,
        location: str | None,
        page: int,
        limit: int,
    ) -> Any:
        raise NotImplementedError
