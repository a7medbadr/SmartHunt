from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime

from smarthunt.database.session import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    actor_id = Column(Integer, nullable=True)

    action = Column(
        String(255),
        nullable=False,
        index=True,
    )

    resource_type = Column(
        String(255),
        nullable=False,
        index=True,
    )

    resource_id = Column(
        String(255),
        nullable=True,
    )

    old_value = Column(
        Text,
        nullable=True,
    )

    new_value = Column(
        Text,
        nullable=True,
    )

    ip_address = Column(
        String(64),
        nullable=True,
    )

    user_agent = Column(
        Text,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        nullable=False,
        index=True,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )
