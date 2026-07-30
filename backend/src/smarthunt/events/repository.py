import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.events.models import EventLog


class EventRepository:

    async def create(
        self,
        db: AsyncSession,
        event_type: str,
        payload: dict,
        status: str = "PUBLISHED",
    ) -> EventLog:

        event = EventLog(
            event_type=event_type,
            payload=json.dumps(payload),
            status=status,
        )

        db.add(event)
        await db.flush()
        await db.refresh(event)

        return event


    async def list_all(
        self,
        db: AsyncSession,
    ) -> list[EventLog]:

        result = await db.execute(
            select(EventLog)
            .order_by(EventLog.created_at.desc())
        )

        return list(result.scalars().all())


event_repository = EventRepository()
