from pydantic import BaseModel
from typing import List, Optional
from smarthunt.shared.pagination import PaginationMeta

class JobItem(BaseModel):
    id: int
    title: str
    location: str
    provider: str
    salary: Optional[int] = None

class SearchResponse(BaseModel):
    items: List[JobItem]
    pagination: PaginationMeta
