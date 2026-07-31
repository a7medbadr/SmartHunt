from fastapi import APIRouter
from smarthunt.recommendation.schemas import RecommendationRequest, RecommendationResponse
from smarthunt.recommendation.service import RecommendationService

router = APIRouter(prefix="/jobs", tags=["Jobs Recommendation"])


@router.post("/recommend", response_model=RecommendationResponse)
def recommend_jobs(request: RecommendationRequest):
    return RecommendationService.recommend_jobs(request.resume)
