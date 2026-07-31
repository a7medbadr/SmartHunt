from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol


@dataclass(slots=True)
class UnknownQuestionRecord:
    provider: str
    url: str
    label: str
    html: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = 0.0


class UnknownQuestionRepository(Protocol):
    """
    Interface. Swap the in-memory implementation below for a
    persistent one later without touching any caller.
    """

    async def save(self, record: UnknownQuestionRecord) -> None: ...

    async def list(
        self,
        provider: str | None = None,
    ) -> list[UnknownQuestionRecord]: ...


class InMemoryUnknownQuestionRepository:

    def __init__(self) -> None:
        self._records: list[UnknownQuestionRecord] = []

    async def save(self, record: UnknownQuestionRecord) -> None:
        self._records.append(record)

    async def list(
        self,
        provider: str | None = None,
    ) -> list[UnknownQuestionRecord]:

        if provider is None:
            return list(self._records)

        return [record for record in self._records if record.provider == provider]

    def clear(self) -> None:
        self._records.clear()


unknown_question_repository = InMemoryUnknownQuestionRepository()
