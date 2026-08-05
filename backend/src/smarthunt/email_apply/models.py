import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base


class EmailMessage(Base):
    """One message in an application's email thread — either the
    original outbound application email, or an inbound reply picked up
    by IMAP polling (see email_apply/service.py::check_for_replies).
    Threading works via real email headers: `message_id` is the Message-ID
    we set when sending, `in_reply_to` is the Message-ID an inbound
    message was replying to — both are how any real mail client threads
    a conversation, not a SmartHunt-specific convention."""

    __tablename__ = "email_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    direction: Mapped[str] = mapped_column(String(20), nullable=False)  # "outbound" | "inbound"
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    to_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    message_id: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    in_reply_to: Mapped[str | None] = mapped_column(String(500), nullable=True)
    read_by_owner: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
