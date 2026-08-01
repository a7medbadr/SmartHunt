from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.settings.models import ProviderSetting


class ProviderSettingsService:

    async def get_enabled_map(self, db: AsyncSession) -> dict[str, bool]:
        """Providers with no explicit row default to enabled."""
        result = await db.execute(select(ProviderSetting))
        return {row.name: row.enabled for row in result.scalars().all()}

    async def set_enabled(self, db: AsyncSession, name: str, enabled: bool) -> ProviderSetting:
        row = await db.get(ProviderSetting, name)
        if row is None:
            row = ProviderSetting(name=name, enabled=enabled)
            db.add(row)
        else:
            row.enabled = enabled
        await db.commit()
        await db.refresh(row)
        return row


provider_settings_service = ProviderSettingsService()
