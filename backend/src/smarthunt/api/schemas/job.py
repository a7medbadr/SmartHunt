from datetime import datetime

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
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
