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
from smarthunt.database.models.job import Job
from smarthunt.database.models.resume import Resume
from smarthunt.database.models.user import User
from smarthunt.resume.api.schemas import (
    ResumeProfileRequest,
    ResumeProfileResponse,
    TailoredResumeResponse,
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
from smarthunt.resume.services.tailoring import (
    generate_tailored_resume as generate_tailored_resume_for_job,
)
from smarthunt.resume.services.tailoring import (
    get_tailored_resume,
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
async def get_resume(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Regression fix: this used to read resume_service.get_resume(),
    which lists whatever file happens to be sitting in the container's
    local STORAGE_DIR (default /tmp/smarthunt/resumes) — completely
    disconnected from the `resumes` DB table the upload endpoint
    actually writes to. Every container restart wipes that ephemeral
    directory, so the Resume page would report "nothing uploaded" even
    though the DB row (and its extracted_text, used by matching/cover
    letter/AI assistant) was still there the whole time. Reads the same
    DB row /resume/text already correctly uses."""

    result = await db.execute(
        select(Resume).where(Resume.user_id == current_user.id).order_by(Resume.updated_at.desc())
    )
    resume = result.scalars().first()

    if resume is None:
        return {"uploaded": False}

    size = None
    path = Path(resume.stored_path)
    if path.exists():
        size = path.stat().st_size

    return {
        "uploaded": True,
        "filename": resume.filename,
        "stored_path": resume.stored_path,
        "size": size,
    }


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
        logger.warning("resume_text_extraction_failed", filename=result["filename"])

    # Found 2026-08-04: a scanned/image-only PDF with no real text layer
    # (pypdf extracts 0 chars from it — not an exception, just an empty
    # string) used to still delete the user's existing, working resume
    # below and replace it with this useless one, since the delete+create
    # happened regardless of whether extraction actually produced
    # anything. Every match score, cover letter, and AI feature reads
    # "whichever resume is most recent" (see search/router.py's
    # _get_resume_text) — one bad upload silently corrupted all of them
    # with no visible error until now. Reject the upload instead, before
    # touching the existing resume, so a bad file can never destroy a
    # working one.
    if not extracted_text or len(extracted_text.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "معرفناش نستخرج نص حقيقي من الملف ده — ممكن يكون PDF ممسوح "
                "ضوئيًا (صورة) من غير طبقة نص حقيقية. جرب ملف PDF فيه نص "
                "فعلي (تقدر تحدده وتنسخه من داخل الملف) أو DOCX بدل منه. "
                "سيرتك الذاتية الحالية لسه محفوظة زي ما هي."
            ),
        )

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


def _job_description_text(job: Job) -> str:
    return "\n".join(part for part in (job.title, job.description, job.requirements) if part)


@router.post(
    "/tailored/{job_id}",
    response_model=TailoredResumeResponse,
    status_code=status.HTTP_200_OK,
)
async def generate_tailored_resume_for_job_endpoint(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generates (or regenerates) a job-specific tailored resume: the real
    uploaded resume kept verbatim plus an AI-written summary targeting
    this job. Pulls the current resume and job straight from the DB
    (both already stored) instead of asking the caller to resend them."""

    resume_result = await db.execute(select(Resume).order_by(Resume.updated_at.desc()).limit(1))
    resume = resume_result.scalars().first()

    if resume is None or not resume.extracted_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No resume uploaded yet.",
        )

    job_result = await db.execute(select(Job).where(Job.id == job_id))
    job = job_result.scalar_one_or_none()

    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    tailored = await generate_tailored_resume_for_job(
        db,
        job_id=job_id,
        resume_text=resume.extracted_text,
        job_description=_job_description_text(job),
    )

    await log_activity(
        db,
        ActivityType.RESUME_UPLOADED,
        f"تم إنشاء سيرة ذاتية مخصصة لوظيفة: {job.title}",
    )

    return tailored


@router.get(
    "/tailored/{job_id}",
    response_model=TailoredResumeResponse,
    status_code=status.HTTP_200_OK,
)
async def get_tailored_resume_for_job_endpoint(
    job_id: int,
    db: AsyncSession = Depends(get_db),
):
    tailored = await get_tailored_resume(db, job_id)

    if tailored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not generated yet.")

    return tailored
