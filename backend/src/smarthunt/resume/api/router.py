import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from smarthunt.resume.parser.extractor import extract_text
from smarthunt.resume.parser.skills import extract_skills
from smarthunt.resume.services.persistence import resume_service

router = APIRouter(tags=["Resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    return await resume_service.upload_resume(file)


@router.get("")
async def get_resume():
    return resume_service.get_resume()


@router.delete("")
async def delete_resume():
    return resume_service.delete_resume()


@router.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    filename = file.filename or ""

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported for analysis.",
        )

    contents = await file.read()

    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(contents)
        tmp.flush()
        text = extract_text(tmp.name)

    skills = extract_skills(text)
    return {"skills": skills}
