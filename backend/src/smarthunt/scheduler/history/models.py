from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base


class SchedulerHistory(Base):
    __tablename__ = "scheduler_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, index=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    jobs_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
