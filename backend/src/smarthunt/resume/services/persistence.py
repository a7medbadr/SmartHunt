from typing import Any, Dict

from fastapi import UploadFile, HTTPException, status

from smarthunt.resume.storage.storage import resume_storage

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
}


class ResumeService:
    """
    Resume application service.
    Handles resume upload, retrieval and deletion operations.
    """

    @staticmethod
    async def upload_resume(
        file: UploadFile,
    ) -> Dict[str, Any]:

        filename = file.filename or ""

        extension = filename.lower().rsplit(
            ".",
            1,
        )[-1]

        ext = f".{extension}"

        if file.content_type not in ALLOWED_MIME_TYPES or ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=("Invalid file format. " "Only PDF and DOCX files are allowed."),
            )

        result = resume_storage.save_resume(
            file.file,
            filename,
        )

        return {
            "status": "uploaded",
            **result,
        }

    @staticmethod
    def get_resume() -> Dict[str, Any]:

        return resume_storage.get_resume_info()

    @staticmethod
    def delete_resume(
        filename: str | None = None,
    ) -> Dict[str, Any]:

        deleted = resume_storage.delete_resume(
            filename,
        )

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume file not found",
            )

        return {
            "status": "deleted",
        }


resume_service = ResumeService()
