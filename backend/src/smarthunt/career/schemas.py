from pydantic import BaseModel
from typing import List

class CareerAdviceRequest(BaseModel):
    resume: str

class CareerAdviceResponse(BaseModel):
    current_level: str
    recommended_roles: List[str]
    skills_to_learn: List[str]
    next_certifications: List[str]
