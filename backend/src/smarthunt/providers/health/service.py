from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.providers.health.models import ProviderHealth
from smarthunt.providers.health.schemas import ProviderHealthUpdate


class ProviderHealthNotFoundError(Exception):
    pass


class ProviderHealthService:
    async def upsert(self, db: AsyncSession, data: ProviderHealthUpdate) -> ProviderHealth:
        result = await db.execute(
            select(ProviderHealth).where(ProviderHealth.provider == data.provider)
        )
        record = result.scalar_one_or_none()

        if record is None:
            record = ProviderHealth(
                provider=data.provider,
                status=data.status,
                response_time_ms=data.response_time_ms,
                message=data.message,
            )
            db.add(record)
        else:
            record.status = data.status
            record.response_time_ms = data.response_time_ms
            record.message = data.message
            record.last_check = datetime.now(timezone.utc).replace(tzinfo=None)

        await db.flush()
        await db.refresh(record)
        return record

    async def list_all(self, db: AsyncSession) -> List[ProviderHealth]:
        result = await db.execute(select(ProviderHealth).order_by(ProviderHealth.provider))
        return list(result.scalars().all())

    async def get_by_provider(self, db: AsyncSession, provider: str) -> ProviderHealth:
        result = await db.execute(select(ProviderHealth).where(ProviderHealth.provider == provider))
        record = result.scalar_one_or_none()
        if record is None:
            raise ProviderHealthNotFoundError(f"No health record for provider '{provider}'")
        return record


provider_health_service = ProviderHealthService()
