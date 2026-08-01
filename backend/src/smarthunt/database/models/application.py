import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = {"extend_existing": True}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="APPLIED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    _AWAITING_RESPONSE_STATUSES = {"applied", "pending"}
    _FOLLOW_UP_AFTER_DAYS = 7

    @property
    def days_since_applied(self) -> int:
        applied_at = self.created_at
        if applied_at.tzinfo is None:
            applied_at = applied_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - applied_at).days

    @property
    def needs_follow_up(self) -> bool:
        return (
            self.status.lower() in self._AWAITING_RESPONSE_STATUSES
            and self.days_since_applied >= self._FOLLOW_UP_AFTER_DAYS
        )
