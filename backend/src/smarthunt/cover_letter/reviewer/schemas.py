from pydantic import BaseModel, Field


class CoverLetterReviewRequest(BaseModel):
    cover_letter: str = Field(..., description="Full text of cover letter to review")


class CoverLetterReviewResponse(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Cover letter quality score out of 100")
    issues: list[str] = Field(default_factory=list, description="List of identified issues")
    recommendations: list[str] = Field(default_factory=list, description="Actionable recommendations")
