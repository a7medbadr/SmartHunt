from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from smarthunt.matching.services.matcher import match

router = APIRouter()


class MatchRequest(BaseModel):
    resume: str = Field(..., description="Resume text or key skills")
    job: str = Field(..., description="Job description or requirements")


class MatchResponse(BaseModel):
    score: float = Field(..., description="Matching score between 0 and 100")
    matched_skills: list[str] = Field(
        default_factory=list, description="Skills present in both resume and job"
    )
    missing_skills: list[str] = Field(
        default_factory=list, description="Skills present in job but missing in resume"
    )


@router.post(
    "/matching",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Calculate match score between resume and job description",
)
async def match_resume_to_job(payload: MatchRequest) -> MatchResponse:
    if not payload.resume.strip() or not payload.job.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both resume and job fields must contain text.",
        )

    result = match(payload.resume, payload.job)
    return MatchResponse(
        score=result["score"],
        matched_skills=result["matched_skills"],
        missing_skills=result["missing_skills"],
    )
