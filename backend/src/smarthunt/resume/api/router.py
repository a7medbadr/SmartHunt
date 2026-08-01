import shutil
from pathlib import Path

import structlog
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pydantic import BaseModel, Field

from smarthunt.activity.models import ActivityType
from smarthunt.activity.service import log_activity
from smarthunt.api.dependencies import get_db
from smarthunt.auth.security import get_current_user
from smarthunt.database.models.resume import Resume
from smarthunt.database.models.user import User
from smarthunt.resume.api.schemas import (
    ResumeProfileRequest,
    ResumeProfileResponse,
)
from smarthunt.resume.parser.parser import extract_text
from smarthunt.resume.parser.skills import extract_skills
from smarthunt.resume.profile_builder import ResumeProfileBuilder
from smarthunt.resume.repositories.repository import ResumeRepository
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

logger = structlog.get_logger("smarthunt")

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


@router.get(
    "/text",
    status_code=status.HTTP_200_OK,
)
async def get_resume_text(db: AsyncSession = Depends(get_db)):
    """The stored resume's already-extracted text — same source
    search/router.py uses for match scoring — so other features (cover
    letter, AI assistant) can use the real uploaded resume instead of
    asking the user to paste it again."""

    result = await db.execute(select(Resume).order_by(Resume.updated_at.desc()).limit(1))
    resume = result.scalar_one_or_none()

    return {"text": resume.extracted_text if resume else None}


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
    current_user: User = Depends(get_current_user),
):

    result = await resume_service.upload_resume(file)

    extracted_text = None
    try:
        extracted_text = extract_text(Path(result["stored_path"]))
    except Exception:
        # A corrupt/unparseable file shouldn't fail the upload — the file
        # itself is still stored and valid; just no extracted text to
        # match against until a readable one is uploaded.
        logger.warning("resume_text_extraction_failed", filename=result["filename"])

    repository = ResumeRepository(db)

    for existing in await repository.get_by_user(current_user.id):
        await repository.delete(existing)

    await repository.create(
        user_id=current_user.id,
        filename=result["filename"],
        stored_path=result["stored_path"],
        extracted_text=extracted_text,
    )

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
async def delete_resume(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    repository = ResumeRepository(db)

    for existing in await repository.get_by_user(current_user.id):
        await repository.delete(existing)

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
