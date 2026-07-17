import os
import shutil
from pathlib import Path
from typing import Any, BinaryIO, Dict, Union

STORAGE_DIR = Path(os.getenv("RESUME_STORAGE_DIR", "/tmp/smarthunt/resumes"))
RESUME_FILE_PATH = STORAGE_DIR / "resume.pdf"


class ResumeStorage:
    def __init__(self) -> None:
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    def save_resume(self, file_obj: Union[BinaryIO, bytes]) -> int:
        self._ensure_storage_dir()
        
        if isinstance(file_obj, bytes):
            RESUME_FILE_PATH.write_bytes(file_obj)
            return len(file_obj)

        if hasattr(file_obj, "seek"):
            file_obj.seek(0)

        with open(RESUME_FILE_PATH, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)

        return RESUME_FILE_PATH.stat().st_size

    def get_resume_path(self) -> Path | None:
        if RESUME_FILE_PATH.exists():
            return RESUME_FILE_PATH
        return None

    def get_resume_info(self) -> Dict[str, Any]:
        if RESUME_FILE_PATH.exists():
            stat = RESUME_FILE_PATH.stat()
            return {
                "uploaded": True,
                "filename": RESUME_FILE_PATH.name,
                "size": stat.st_size,
            }
        return {"uploaded": False}

    def delete_resume(self) -> bool:
        if RESUME_FILE_PATH.exists():
            RESUME_FILE_PATH.unlink()
            return True
        return False


resume_storage = ResumeStorage()
