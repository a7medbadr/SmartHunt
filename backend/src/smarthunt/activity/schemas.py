from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from smarthunt.activity.models import ActivityType

class ActivityCreate(BaseModel):
    type: ActivityType
    title: str = Field(..., max_length=255)
    details: Optional[str] = None

class ActivityResponse(BaseModel):
    id: int
    type: ActivityType
    title: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
