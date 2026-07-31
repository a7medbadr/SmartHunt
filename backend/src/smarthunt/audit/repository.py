from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.audit.models import AuditLog


class AuditRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        audit: AuditLog,
    ) -> AuditLog:
        self.db.add(audit)
        await self.db.flush()
        await self.db.refresh(audit)
        return audit

    async def get_logs(
        self,
        action: str | None = None,
        resource_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ):

        query = select(AuditLog)

        if action:
            query = query.where(AuditLog.action == action)

        if resource_type:
            query = query.where(AuditLog.resource_type == resource_type)

        if date_from:
            query = query.where(AuditLog.created_at >= date_from)

        if date_to:
            query = query.where(AuditLog.created_at <= date_to)

        query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)

        return list(result.scalars().all())
