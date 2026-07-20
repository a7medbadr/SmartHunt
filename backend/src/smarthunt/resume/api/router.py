import shutil

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)

from pydantic import BaseModel, Field

from smarthunt.resume.parser.parser import extract_text
from smarthunt.resume.parser.skills import extract_skills

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

router.include_router(
    reviewer_router
)


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
):

    return await resume_service.upload_resume(
        file
    )


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


    temp_path = STORAGE_DIR / (
        f"temp_{file.filename}"
    )


    try:

        with open(
            temp_path,
            "wb",
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer,
            )


        text = extract_text(
            temp_path
        )

        skills = extract_skills(
            text
        )


        return ResumeAnalyzeResponse(
            skills=skills
        )


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

    return ResumeGenerateResponse(
        **result
    )
