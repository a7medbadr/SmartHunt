from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MonitoredAccountCreate(BaseModel):
    profile_url: str
    label: str | None = None


class MonitoredAccountUpdate(BaseModel):
    enabled: bool


class MonitoredAccountResponse(BaseModel):
    id: int
    profile_url: str
    label: str | None
    enabled: bool
    last_checked_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScanResultResponse(BaseModel):
    scanned: int
    saved: int
    job_ids: list[int]


class MonitoredHashtagCreate(BaseModel):
    tag: str


class MonitoredHashtagUpdate(BaseModel):
    enabled: bool


class MonitoredHashtagResponse(BaseModel):
    id: int
    tag: str
    enabled: bool
    last_checked_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
