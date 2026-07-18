import shutil
from fastapi import APIRouter, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from smarthunt.resume.parser.parser import extract_text
from smarthunt.resume.parser.skills import extract_skills
from smarthunt.resume.reviewer.router import router as reviewer_router
from smarthunt.resume.services.generator import generate_resume
from smarthunt.resume.storage.storage import (
    STORAGE_DIR,
    resume_storage,
)

router = APIRouter()
router.include_router(reviewer_router)


class ResumeGenerateRequest(BaseModel):
    resume: str = Field(..., description="Original resume text")
    job: str = Field(..., description="Target job description text")


class ResumeGenerateResponse(BaseModel):
    score: int
    matched_skills: list[str]
    recommended_skills: list[str]
    generated_resume: str


class ResumeAnalyzeResponse(BaseModel):
    skills: list[str]


@router.get("", status_code=status.HTTP_200_OK)
def get_resume():
    return resume_storage.get_resume_info()


@router.post("", status_code=status.HTTP_200_OK)
@router.post("/upload", status_code=status.HTTP_200_OK)
def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    content = file.file.read()
    file.file.seek(0)

    resume_storage.save_resume(file.file)
    return {
        "status": "uploaded",
        "size": len(content),
    }


@router.delete("", status_code=status.HTTP_200_OK)
def delete_resume():
    deleted = resume_storage.delete_resume()
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found",
        )
    return {"status": "deleted"}


@router.post(
    "/analyze",
    response_model=ResumeAnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    temp_path = STORAGE_DIR / f"temp_{file.filename}"

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        text = extract_text(temp_path)
        skills = extract_skills(text)
        return ResumeAnalyzeResponse(skills=skills)
    finally:
        if temp_path.exists():
            temp_path.unlink()


@router.post(
    "/generate",
    response_model=ResumeGenerateResponse,
    status_code=status.HTTP_200_OK,
)
def generate_tailored_resume(payload: ResumeGenerateRequest):
    result = generate_resume(
        resume_text=payload.resume,
        job_description=payload.job,
    )
    return ResumeGenerateResponse(**result)
