from pydantic import BaseModel


class CoverLetterGenerateRequest(BaseModel):
    resume: str
    job: str


class CoverLetterGenerateResponse(BaseModel):
    score: int
    matched_skills: list[str]
    generated_cover_letter: str
