from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MonitoredChatCreate(BaseModel):
    chat_url: str
    label: str
    chat_type: str = "channel"  # "channel" | "group"


class MonitoredChatUpdate(BaseModel):
    enabled: bool


class MonitoredChatResponse(BaseModel):
    id: int
    chat_url: str
    label: str
    chat_type: str
    enabled: bool
    last_checked_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanResultResponse(BaseModel):
    scanned: int
    saved: int
    job_ids: list[int]


class WhatsAppLoginStatusResponse(BaseModel):
    logged_in: bool
