from datetime import datetime

from pydantic import BaseModel


class EventResponse(BaseModel):
    id: int
    event_type: str
    payload: str
    status: str
    created_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True
