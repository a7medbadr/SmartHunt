import json
from hashlib import sha256

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.idempotency.models import IdempotencyKey
from smarthunt.metrics.idempotency import (
    duplicate_requests_prevented_total,
    idempotency_created_total,
    idempotency_hits_total,
)


class IdempotencyService:

    async def build_key(
        self,
        provider: str,
        company: str,
        job_url: str,
        user: str,
    ) -> str:

        raw = "|".join(
            [
                provider.lower(),
                company.lower(),
                job_url.lower(),
                user.lower(),
            ]
        )

        return sha256(
            raw.encode(),
        ).hexdigest()

    async def get(
        self,
        db: AsyncSession,
        key: str,
    ) -> IdempotencyKey | None:

        result = await db.execute(select(IdempotencyKey).where(IdempotencyKey.key == key))

        return result.scalar_one_or_none()

    async def create(
        self,
        db: AsyncSession,
        key: str,
    ) -> IdempotencyKey:

        record = IdempotencyKey(
            key=key,
            status="RUNNING",
        )

        db.add(record)

        await db.flush()
        await db.refresh(record)

        idempotency_created_total.inc()

        return record

    async def complete(
        self,
        db: AsyncSession,
        key: str,
        response: dict,
    ) -> None:

        record = await self.get(
            db,
            key,
        )

        if record is None:
            return

        record.status = "SUCCESS"
        record.response = json.dumps(response)

        await db.flush()

    async def get_or_create(
        self,
        db: AsyncSession,
        key: str,
    ) -> tuple[bool, IdempotencyKey]:

        existing = await self.get(
            db,
            key,
        )

        if existing:

            idempotency_hits_total.inc()
            duplicate_requests_prevented_total.inc()

            return True, existing

        created = await self.create(
            db,
            key,
        )

        return False, created


idempotency_service = IdempotencyService()
