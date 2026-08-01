from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, HttpUrl


class JobCreate(BaseModel):
    title: str
    company: str
    location: str
    source: str
    url: HttpUrl


class JobResponse(BaseModel):
    id: int
    title: str
    company: str
    location: str
    source: str
    url: HttpUrl
    description: Optional[str] = None
    requirements: Optional[str] = None
    created_at: datetime
    no_sponsorship_signal: bool = False

    model_config = ConfigDict(from_attributes=True)
