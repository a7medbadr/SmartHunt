from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SortField(str, Enum):
    TITLE = "title"
    SALARY = "salary"
    SCORE = "score"
    CREATED_AT = "created_at"


class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SearchJobQueryParams(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = Field(None, description="Filter by job title")
    company: Optional[str] = Field(None, description="Filter by company name")
    location: Optional[str] = Field(None, description="Filter by location")
    provider: Optional[str] = Field(None, description="Filter by provider name")
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    score_min: Optional[float] = Field(None, ge=0, le=100)
    sort: SortField = Field(default=SortField.SCORE)
    order: SortOrder = Field(default=SortOrder.DESC)
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=10, ge=1, le=100)


class SearchHistoryResponse(BaseModel):
    id: int
    query: Optional[str] = None
    provider: Optional[str] = None
    location: Optional[str] = None
    results_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)
