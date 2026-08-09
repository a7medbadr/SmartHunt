from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base
from smarthunt.matching.services.job_signals import detect_no_sponsorship


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    company: Mapped[str] = mapped_column(String, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # Set only for jobs discovered from a LinkedIn post (source="linkedin_post")
    # rather than the structured Jobs search page — the post's own permalink,
    # shown distinctly on the job detail page. Non-null is the signal that
    # this job came from a post, not a listing.
    post_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    # When the job was actually posted on the source site — distinct from
    # created_at below (when SmartHunt discovered/scraped it). Only
    # LinkedIn's real provider currently populates this; null otherwise.
    posted_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    # The owner's own triage of a discovered job — "applied" (a real
    # Application row is also created, see api/routes/jobs.py) or
    # "not_suitable" (dismissed but kept for reference, not deleted).
    # Null means not yet reviewed. Deliberately a separate field from
    # Application.status (a richer, multi-stage pipeline status on the
    # Application entity itself) — this is a lightweight, fast-filterable
    # flag on the Job row for the discovered-jobs tabs' own list view.
    review_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    @property
    def no_sponsorship_signal(self) -> bool:
        return detect_no_sponsorship(f"{self.description or ''} {self.requirements or ''}")
