from datetime import date, datetime
from typing import Literal, Optional

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
    posted_at: Optional[date] = None
    post_url: Optional[str] = None
    no_sponsorship_signal: bool = False
    review_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobReviewStatusUpdate(BaseModel):
    review_status: Optional[Literal["applied", "not_suitable"]] = None
