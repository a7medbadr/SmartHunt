from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from smarthunt.database.session import Base


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    keyword = Column(String, nullable=True)
    location = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
