from pydantic import BaseModel
from typing import List, Optional

class JobItem(BaseModel):
    id: int
    title: str
    location: str
    provider: str
    salary: Optional[int] = None
    experience: Optional[str] = None
    remote: Optional[bool] = None
    onsite: Optional[bool] = None
    hybrid: Optional[bool] = None
    country: Optional[str] = None
    city: Optional[str] = None
    score: Optional[float] = 0.0

class SearchResponse(BaseModel):
    items: List[JobItem]
    total: int
    page: int
    limit: int
    pages: int
