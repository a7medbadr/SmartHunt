from fastapi import APIRouter, UploadFile, File

from smarthunt.resume.storage.storage import save_resume
from smarthunt.resume.parser.parser import extract_text

router = APIRouter()


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    path = save_resume(
        file.filename,
        await file.read(),
    )

    text = extract_text(path)

    return {
        "filename": file.filename,
        "stored_as": str(path),
        "characters": len(text),
        "preview": text[:500],
    }
