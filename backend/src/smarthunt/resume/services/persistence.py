import os
from typing import Dict, Any
from fastapi import UploadFile, HTTPException, status
from smarthunt.resume.storage.storage import resume_storage

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class ResumeService:
    @staticmethod
    async def upload_resume(file: UploadFile) -> Dict[str, Any]:
        filename = file.filename or ""
        ext = os.path.splitext(filename)[1].lower()

        # Validate MIME type and file extension
        if file.content_type not in ALLOWED_MIME_TYPES or ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only PDF and DOCX files are allowed.",
            )

        file_size = resume_storage.save_resume(file.file)

        return {
            "status": "uploaded",
            "filename": "resume.pdf",
            "size": file_size,
        }

    @staticmethod
    def get_resume() -> Dict[str, Any]:
        return resume_storage.get_resume_info()

    @staticmethod
    def delete_resume() -> Dict[str, Any]:
        resume_storage.delete_resume()
        return {"status": "deleted"}


resume_service = ResumeService()
