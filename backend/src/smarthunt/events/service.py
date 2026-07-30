from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.events.repository import event_repository
from smarthunt.events.base import BaseEvent
from smarthunt.metrics.events import (
    events_failed_total,
    events_published_total,
    events_processed_total,
)


class EventService:

    async def publish(
        self,
        db: AsyncSession,
        event: BaseEvent,
    ):

        try:
            record = await event_repository.create(
                db=db,
                event_type=event.event_type,
                payload=event.payload,
            )

            events_published_total.inc()
            events_processed_total.inc()

            return record

        except Exception:
            events_failed_total.inc()
            raise


event_service = EventService()
