from fastapi import APIRouter, status
from pydantic import BaseModel, Field

from smarthunt.matching.job_parser import extract_job_skills
from smarthunt.resume.parser.skills import extract_skills

router = APIRouter()


class JobAnalyzeRequest(BaseModel):
    description: str = Field(..., description="Job Description text")


class JobAnalyzeResponse(BaseModel):
    skills: list[str]


class MatchingAnalyzeRequest(BaseModel):
    resume: str = Field(..., description="Resume text or extracted skills text")
    job: str = Field(..., description="Job description text")


class MatchingAnalyzeResponse(BaseModel):
    score: int
    matched_skills: list[str]
    missing_skills: list[str]


@router.post(
    "/jobs/analyze",
    response_model=JobAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    tags=["Jobs"],
)
def analyze_job(payload: JobAnalyzeRequest):
    skills = extract_job_skills(payload.description)
    return JobAnalyzeResponse(skills=skills)


@router.post(
    "/matching/analyze",
    response_model=MatchingAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching"],
)
@router.post(
    "/matching",
    response_model=MatchingAnalyzeResponse,
    status_code=status.HTTP_200_OK,
    tags=["Matching"],
)
def analyze_matching(payload: MatchingAnalyzeRequest):
    resume_skills = set(extract_skills(payload.resume))
    job_skills = set(extract_job_skills(payload.job))

    if not job_skills:
        return MatchingAnalyzeResponse(
            score=0,
            matched_skills=[],
            missing_skills=[],
        )

    matched = sorted(list(resume_skills.intersection(job_skills)))
    missing = sorted(list(job_skills.difference(resume_skills)))

    score = int((len(matched) / len(job_skills)) * 100)

    return MatchingAnalyzeResponse(
        score=score,
        matched_skills=matched,
        missing_skills=missing,
    )
