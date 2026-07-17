from fastapi import APIRouter, File, UploadFile
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
