from pydantic import BaseModel
from typing import List


class RecommendationRequest(BaseModel):
    resume: str


class JobRecommendation(BaseModel):
    title: str
    score: int


class RecommendationResponse(BaseModel):
    recommendations: List[JobRecommendation]
