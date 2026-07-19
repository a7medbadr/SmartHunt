from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.settings.schemas import SettingsResponse, SettingsUpdate
from smarthunt.settings.service import settings_service

router = APIRouter(prefix="", tags=["settings"])


@router.put("", response_model=SettingsResponse)
async def update_settings(payload: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    return await settings_service.upsert(db, payload)


@router.get("", response_model=SettingsResponse)
async def get_settings(db: AsyncSession = Depends(get_db)):
    return await settings_service.get(db)
