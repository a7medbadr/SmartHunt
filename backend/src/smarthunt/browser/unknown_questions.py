from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from sqlalchemy import DateTime, Float, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base
from smarthunt.database.session import AsyncSessionLocal


class UnknownQuestion(Base):
    """Persisted record of an Easy Apply question the rule-based answerer
    couldn't handle, causing the application to pause. Previously kept
    only in an in-memory list (InMemoryUnknownQuestionRepository below,
    still used by tests) — lost on every restart, so the owner had no way
    to look back at what actually blocked a paused application."""

    __tablename__ = "unknown_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String, nullable=False)
    label: Mapped[str] = mapped_column(String, nullable=False)
    html: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


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


class DBUnknownQuestionRepository:
    """Real implementation — persists to the `unknown_questions` table so
    a paused application's blocking question survives a restart, instead
    of only living in a process-local list. Opens its own session (same
    pattern as scheduler/jobs.py's periodic jobs) since this is called
    from deep inside the Easy Apply fill loop, which has no request-scoped
    db session threaded through it."""

    async def save(self, record: UnknownQuestionRecord) -> None:
        async with AsyncSessionLocal() as db:
            db.add(
                UnknownQuestion(
                    provider=record.provider,
                    url=record.url,
                    label=record.label,
                    html=record.html,
                    confidence=record.confidence,
                )
            )
            await db.commit()

    async def list(
        self,
        provider: str | None = None,
    ) -> list[UnknownQuestionRecord]:

        async with AsyncSessionLocal() as db:
            query = select(UnknownQuestion)

            if provider is not None:
                query = query.where(UnknownQuestion.provider == provider)

            result = await db.execute(query.order_by(UnknownQuestion.created_at.desc()))

            return [
                UnknownQuestionRecord(
                    provider=row.provider,
                    url=row.url,
                    label=row.label,
                    html=row.html,
                    confidence=row.confidence,
                    timestamp=row.created_at.replace(tzinfo=timezone.utc),
                )
                for row in result.scalars().all()
            ]


unknown_question_repository: UnknownQuestionRepository = DBUnknownQuestionRepository()
