from pydantic import BaseModel


class JobSearchFilters(BaseModel):
    keyword: str | None = None
    company: str | None = None
    location: str | None = None
    source: str | None = None
