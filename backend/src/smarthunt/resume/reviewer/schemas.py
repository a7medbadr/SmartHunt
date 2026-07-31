from pydantic import BaseModel, Field


class ResumeReviewRequest(BaseModel):
    resume: str = Field(..., description="Full text of the resume to review")


class ResumeReviewResponse(BaseModel):
    ats_score: int = Field(..., ge=0, le=100, description="ATS score out of 100")
    strengths: list[str] = Field(default_factory=list, description="Key strengths identified")
    weaknesses: list[str] = Field(
        default_factory=list, description="Identified weaknesses or missing elements"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Actionable recommendations"
    )
