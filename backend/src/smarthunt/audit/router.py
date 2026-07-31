from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.audit.schemas import AuditLogResponse
from smarthunt.audit.service import AuditService
from smarthunt.database.session import get_db

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
)


@router.get(
    "/logs",
    response_model=list[AuditLogResponse],
)
async def get_audit_logs(
    action: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, le=100),
    db: AsyncSession = Depends(get_db),
):

    service = AuditService(db)

    return await service.repository.get_logs(
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )
