import shutil

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, Field

from smarthunt.activity.models import ActivityType
from smarthunt.activity.service import log_activity
from smarthunt.api.dependencies import get_db
from smarthunt.resume.api.schemas import (
    ResumeProfileRequest,
    ResumeProfileResponse,
)
from smarthunt.resume.parser.parser import extract_text
from smarthunt.resume.parser.skills import extract_skills
from smarthunt.resume.profile_builder import ResumeProfileBuilder
from smarthunt.resume.reviewer.router import (
    router as reviewer_router,
)
from smarthunt.resume.services.generator import (
    generate_resume,
)
from smarthunt.resume.services.persistence import (
    resume_service,
)
from smarthunt.resume.storage.storage import (
    STORAGE_DIR,
)

router = APIRouter()

router.include_router(reviewer_router)


class ResumeGenerateRequest(BaseModel):
    resume: str = Field(
        ...,
        description="Original resume text",
    )

    job: str = Field(
        ...,
        description="Target job description text",
    )


class ResumeGenerateResponse(BaseModel):
    score: int
    matched_skills: list[str]
    recommended_skills: list[str]
    generated_resume: str


class ResumeAnalyzeResponse(BaseModel):
    skills: list[str]


@router.post(
    "/profile",
    response_model=ResumeProfileResponse,
    status_code=status.HTTP_200_OK,
)
def build_resume_profile(
    payload: ResumeProfileRequest,
):
    profile = ResumeProfileBuilder().build(payload.resume)
    return ResumeProfileResponse(**profile.to_dict())


@router.get(
    "",
    status_code=status.HTTP_200_OK,
)
def get_resume():

    return resume_service.get_resume()


@router.post(
    "",
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/upload",
    status_code=status.HTTP_200_OK,
)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):

    result = await resume_service.upload_resume(file)

    await log_activity(
        db,
        ActivityType.RESUME_UPLOADED,
        f"تم رفع سيرة ذاتية: {file.filename}",
    )

    return result


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
)
def delete_resume():

    return resume_service.delete_resume()


@router.post(
    "/analyze",
    response_model=ResumeAnalyzeResponse,
    status_code=status.HTTP_200_OK,
)
def analyze_resume(
    file: UploadFile = File(...),
):

    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are allowed",
        )

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = STORAGE_DIR / (f"temp_{file.filename}")

    try:

        with open(
            temp_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )

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
def generate_tailored_resume(
    payload: ResumeGenerateRequest,
):

    result = generate_resume(
        resume_text=payload.resume,
        job_description=payload.job,
    )

    return ResumeGenerateResponse(**result)
