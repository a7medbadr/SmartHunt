from pydantic import BaseModel
from typing import List, Optional

class JobItem(BaseModel):
    id: int
    title: str
    location: str
    provider: str
    salary: Optional[int] = None

class SearchResponse(BaseModel):
    items: List[JobItem]
    count: int
    page: int
