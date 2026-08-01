from typing import Optional
from pydantic import BaseModel, ConfigDict


class SearchHistoryResponse(BaseModel):
    id: int
    query: Optional[str] = None
    provider: Optional[str] = None
    location: Optional[str] = None
    results_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)
