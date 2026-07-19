import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, Text, Enum as SQLEnum

from smarthunt.database.session import Base


class ActivityType(str, enum.Enum):
    RESUME_UPLOADED = "resume_uploaded"
    APPLICATION_CREATED = "application_created"
    FAVORITE_ADDED = "favorite_added"
    SAVED_SEARCH_CREATED = "saved_search_created"
    COVER_LETTER_GENERATED = "cover_letter_generated"


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(SQLEnum(ActivityType), nullable=False)
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        nullable=False,
        index=True,
    )
