from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base


class MonitoredWhatsAppChat(Base):
    """A WhatsApp channel or group (e.g. "ELITE IT | وظائف تقنية معلومات -
    السعودية") the owner has already joined, whose messages get
    periodically scanned for job-relevant content — the WhatsApp
    counterpart to linkedin_monitor.MonitoredLinkedInAccount. Channels and
    groups behave identically for scanning purposes (both are just "an
    already-joined chat to open and read"), unlike LinkedIn's genuinely
    different account/hashtag page types, so this is a single table.

    label is REQUIRED (unlike MonitoredLinkedInAccount.label): day-to-day
    scans locate the chat by searching this exact display name in
    WhatsApp Web's own sidebar search, not by URL — WhatsApp Web has no
    stable per-chat URL the way LinkedIn has per-profile URLs. chat_url
    (the invite link) is only ever used once, to join the chat manually
    before adding it here."""

    __tablename__ = "monitored_whatsapp_chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    chat_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "channel" | "group"
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
