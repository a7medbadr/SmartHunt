from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from smarthunt.database.base import Base


class ProviderHealth(Base):
    __tablename__ = "provider_health"

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
    last_check: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=True)
