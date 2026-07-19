from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base

try:
    from smarthunt.database.session import Base
except ImportError:
    Base = declarative_base()


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    keyword = Column(String, nullable=True)
    location = Column(String, nullable=True)
    source = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
