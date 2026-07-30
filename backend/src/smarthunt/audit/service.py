from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.audit.models import AuditLog
from smarthunt.audit.repository import AuditRepository


class AuditService:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.repository = AuditRepository(db)


    async def log(
        self,
        action: str,
        resource: str,
        resource_id: str | int | None = None,
        actor_id: int | None = None,
        old_value: str | None = None,
        new_value: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ):

        audit = AuditLog(
            actor_id=actor_id,
            action=action,
            resource_type=resource,
            resource_id=str(resource_id) if resource_id else None,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return await self.repository.create(audit)
