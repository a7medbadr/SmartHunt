from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base


class MonitoredLinkedInAccount(Base):
    """A LinkedIn profile whose posts (and reposts) get periodically
    scanned for job-relevant content — the "HR/recruiter posted a job on
    LinkedIn instead of the Jobs tab" discovery path, distinct from the
    normal job-search-page scraping in providers/linkedin/provider.py."""

    __tablename__ = "monitored_linkedin_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class MonitoredHashtag(Base):
    """A LinkedIn hashtag whose first ~50 posts get periodically scanned
    for job-relevant content — moved 2026-08-06 from a hardcoded Python
    list (scheduler/jobs.py's old HASHTAG_LIST) to a real, owner-editable
    DB table per explicit request, mirroring MonitoredLinkedInAccount
    above exactly: each hashtag can be individually enabled/disabled,
    scanned on demand, or removed, instead of only being editable by
    changing code."""

    __tablename__ = "monitored_hashtags"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
