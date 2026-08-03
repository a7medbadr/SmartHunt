from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.api.dependencies import get_db
from smarthunt.providers.registry import provider_registry
from smarthunt.providers.settings.schemas import ProviderInfo, ProviderSettingUpdate
from smarthunt.providers.settings.service import provider_settings_service

router = APIRouter(prefix="/providers", tags=["providers"])

# Providers whose search() does real scraping/API calls, as opposed to
# still-hardcoded placeholder data. Update this set as more get built —
# see CLAUDE.md's provider capability notes. Never advertise a fake
# provider as real; that's exactly the "looks real but isn't" pattern
# this whole codebase has had to keep fixing.
REAL_DISCOVERY_PROVIDERS = {"linkedin", "sabbar"}


@router.get("", response_model=list[ProviderInfo])
async def list_providers(db: AsyncSession = Depends(get_db)):
    enabled_map = await provider_settings_service.get_enabled_map(db)

    return [
        ProviderInfo(
            name=p.name,
            enabled=enabled_map.get(p.name, True),
            supports_login=p.supports_login,
            supports_apply=p.supports_apply,
            supports_resume_upload=p.supports_resume_upload,
            supports_cover_letter=p.supports_cover_letter,
            real_discovery=p.name in REAL_DISCOVERY_PROVIDERS,
        )
        for p in provider_registry.providers()
    ]


@router.patch("/{name}", response_model=ProviderInfo)
async def update_provider(
    name: str, payload: ProviderSettingUpdate, db: AsyncSession = Depends(get_db)
):
    all_providers = {p.name: p for p in provider_registry.providers()}

    if name not in all_providers:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown provider")

    await provider_settings_service.set_enabled(db, name, payload.enabled)

    p = all_providers[name]

    return ProviderInfo(
        name=p.name,
        enabled=payload.enabled,
        supports_login=p.supports_login,
        supports_apply=p.supports_apply,
        supports_resume_upload=p.supports_resume_upload,
        supports_cover_letter=p.supports_cover_letter,
        real_discovery=p.name in REAL_DISCOVERY_PROVIDERS,
    )
