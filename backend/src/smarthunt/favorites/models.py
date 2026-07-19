from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from smarthunt.database.session import Base


class FavoriteJob(Base):
    __tablename__ = "favorite_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True, default="N/A")
    source = Column(String, nullable=True, default="N/A")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
