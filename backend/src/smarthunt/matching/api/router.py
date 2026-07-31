from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from smarthunt.ai.exceptions import AIError
from smarthunt.matching.services.deep_analysis import generate_deep_analysis
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


class DeepAnalysisResponse(BaseModel):
    score: int
    matched_skills: list[str]
    missing_skills: list[str]
    ai_summary: str
    provider: str
    success: bool


@router.post("/deep-analysis", status_code=status.HTTP_200_OK)
async def deep_analysis(payload: MatchRequest) -> DeepAnalysisResponse:
    if not payload.resume.strip() or not payload.job.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both resume and job fields must contain text.",
        )

    try:
        result = await generate_deep_analysis(payload.resume, payload.job)
    except AIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI analysis failed: {exc}",
        ) from exc

    return DeepAnalysisResponse(
        score=result.score,
        matched_skills=result.matched_skills,
        missing_skills=result.missing_skills,
        ai_summary=result.ai_summary,
        provider=result.provider,
        success=result.success,
    )
