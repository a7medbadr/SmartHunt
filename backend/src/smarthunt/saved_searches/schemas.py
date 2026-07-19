from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SavedSearchCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the saved search")
    keyword: Optional[str] = None
    location: Optional[str] = None


class SavedSearchResponse(BaseModel):
    id: int
    name: str
    keyword: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
