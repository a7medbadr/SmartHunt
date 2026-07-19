from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.providers.health.schemas import (
    ProviderHealthDetail,
    ProviderHealthResponse,
    ProviderHealthUpdate,
)
from smarthunt.providers.health.service import (
    ProviderHealthNotFoundError,
    provider_health_service,
)

router = APIRouter(prefix="", tags=["provider-health"])


@router.post("", response_model=ProviderHealthResponse, status_code=status.HTTP_201_CREATED)
async def update_provider_health(payload: ProviderHealthUpdate, db: AsyncSession = Depends(get_db)):
    return await provider_health_service.upsert(db, payload)


@router.get("", response_model=List[ProviderHealthDetail])
async def list_provider_health(db: AsyncSession = Depends(get_db)):
    return await provider_health_service.list_all(db)


@router.get("/{provider}", response_model=ProviderHealthDetail)
async def get_provider_health(provider: str, db: AsyncSession = Depends(get_db)):
    try:
        return await provider_health_service.get_by_provider(db, provider)
    except ProviderHealthNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
