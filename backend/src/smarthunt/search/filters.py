from pydantic import BaseModel
from typing import Optional

class JobFilters(BaseModel):
    experience: Optional[str] = None
    remote: Optional[bool] = None
    onsite: Optional[bool] = None
    hybrid: Optional[bool] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
