from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.settings.models import UserSettings
from smarthunt.settings.schemas import SettingsUpdate


class SettingsService:
    async def get(self, db: AsyncSession) -> UserSettings:
        result = await db.execute(select(UserSettings).order_by(UserSettings.id).limit(1))
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = UserSettings()
            db.add(settings)
            await db.flush()
            await db.refresh(settings)
        return settings

    async def upsert(self, db: AsyncSession, data: SettingsUpdate) -> UserSettings:
        result = await db.execute(select(UserSettings).order_by(UserSettings.id).limit(1))
        settings = result.scalar_one_or_none()

        if settings is None:
            settings = UserSettings(
                theme=data.theme,
                language=data.language,
                email_notifications=data.email_notifications,
                job_alerts=data.job_alerts,
            )
            db.add(settings)
        else:
            settings.theme = data.theme
            settings.language = data.language
            settings.email_notifications = data.email_notifications
            settings.job_alerts = data.job_alerts

        await db.flush()
        await db.refresh(settings)
        return settings


settings_service = SettingsService()
