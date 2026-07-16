from pydantic import BaseModel
from typing import Optional

class SearchJobItem(BaseModel):
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
    match_details: Optional[dict] = None

class SearchResult:
    def __init__(self, items: list, total: int, page: int, limit: int):
        self.items = items
        self.total = total
        self.page = page
        self.limit = limit
        self.pages = (total + limit - 1) // limit if limit > 0 else 1
