import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.idempotency.service import idempotency_service

router = APIRouter(
    prefix="",
    tags=["idempotency"],
)


@router.get("/{key}")
async def get_idempotency(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    record = await idempotency_service.get(
        db,
        key,
    )

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Idempotency key not found",
        )

    response = None

    if record.response:
        response = json.loads(
            record.response,
        )

    return {
        "key": record.key,
        "status": record.status,
        "response": response,
        "created_at": record.created_at,
        "expires_at": record.expires_at,
    }
