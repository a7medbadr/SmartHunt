from fastapi import APIRouter
from pydantic import BaseModel
from smarthunt.matching.services.matcher import match

router = APIRouter(prefix="/matching", tags=["matching"])


class MatchRequest(BaseModel):
    resume: str
    job: str


class MatchResponse(BaseModel):
    score: int
    matched_skills: list[str]
    missing_skills: list[str]


@router.post("", response_model=MatchResponse)
async def match_resume_to_job(payload: MatchRequest):
    return match(resume_text=payload.resume, job_text=payload.job)
