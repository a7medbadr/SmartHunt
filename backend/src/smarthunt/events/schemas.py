from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventResponse(BaseModel):
    id: int
    event_type: str
    payload: str
    status: str
    created_at: datetime
    processed_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )
