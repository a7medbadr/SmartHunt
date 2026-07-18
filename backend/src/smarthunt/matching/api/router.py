from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from smarthunt.matching.services.matcher import match

router = APIRouter()


class MatchRequest(BaseModel):
    resume: str = Field(..., description="Resume text or key skills")
    job: str = Field(..., description="Job description or requirements")


class MatchResponse(BaseModel):
    score: float = Field(..., description="Matching score between 0 and 100")
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)


def _run_match(payload: MatchRequest) -> MatchResponse:
    if not payload.resume.strip() or not payload.job.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both resume and job fields must contain text.",
        )
    result = match(payload.resume, payload.job)
    return MatchResponse(**result)


@router.post("", status_code=status.HTTP_200_OK)
@router.post("/", status_code=status.HTTP_200_OK)
def match_resume_job(payload: MatchRequest) -> MatchResponse:
    return _run_match(payload)


@router.post("/analyze", status_code=status.HTTP_200_OK)
def analyze_match(payload: MatchRequest) -> MatchResponse:
    return _run_match(payload)
