from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from smarthunt.database.base import Base


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    query = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    location = Column(String, nullable=True)
    results_count = Column(Integer, default=0)
    filters = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="search_histories", lazy="joined")


SearchHistoryModel = SearchHistory
