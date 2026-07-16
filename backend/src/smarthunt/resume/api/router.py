from fastapi import APIRouter, UploadFile, File

from smarthunt.resume.storage.storage import save_resume

router = APIRouter()


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    path = save_resume(
        file.filename,
        await file.read(),
    )

    return {
        "filename": file.filename,
        "stored_as": str(path),
    }
