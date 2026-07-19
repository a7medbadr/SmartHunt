from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, Field


class FavoriteJobCreate(BaseModel):
    job_id: Union[int, str] = Field(..., description="ID of the target job")
    title: str = Field(..., min_length=1, description="Title of the job")
    company: Optional[str] = "N/A"
    source: Optional[str] = "N/A"


class FavoriteJobResponse(BaseModel):
    id: int
    job_id: str
    title: str
    company: Optional[str] = "N/A"
    source: Optional[str] = "N/A"
    created_at: datetime

    class Config:
        from_attributes = True
