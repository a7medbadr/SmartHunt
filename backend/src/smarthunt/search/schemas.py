from pydantic import BaseModel
from typing import List, Optional

class PaginationMeta(BaseModel):
    total: int
    page: int
    limit: int
    pages: int

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

class SearchResponse(BaseModel):
    items: List[JobItem]
    total: int
    page: int
    limit: int
    pages: int
