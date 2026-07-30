from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    user_id: int | None = None
    type: str = Field(default="INFO")
    title: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    channel: str = Field(default="IN_APP")
    priority: str = Field(default="NORMAL")
    expires_at: datetime | None = None


class NotificationResponse(BaseModel):
    id: int
    user_id: int | None
    type: str
    title: str
    message: str
    status: str
    channel: str
    priority: str
    created_at: datetime
    read_at: datetime | None
    expires_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
