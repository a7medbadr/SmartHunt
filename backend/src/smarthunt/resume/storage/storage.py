import shutil
from pathlib import Path
from typing import Dict, Any

# Target path: backend/storage/resumes/
BASE_DIR = Path(__file__).resolve().parents[4]  # Points to project root
STORAGE_DIR = BASE_DIR / "backend" / "storage" / "resumes"
RESUME_FILE_PATH = STORAGE_DIR / "resume.pdf"


class ResumeStorage:
    def __init__(self) -> None:
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Create backend/storage/resumes if it does not exist."""
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    def save_resume(self, file_obj) -> int:
        """Saves or replaces resume.pdf and returns file size."""
        self._ensure_storage_dir()
        with open(RESUME_FILE_PATH, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
        return RESUME_FILE_PATH.stat().st_size

    def get_resume_info(self) -> Dict[str, Any]:
        """Returns metadata about current resume."""
        if RESUME_FILE_PATH.exists():
            return {
                "uploaded": True,
                "filename": RESUME_FILE_PATH.name,
                "size": RESUME_FILE_PATH.stat().st_size,
            }
        return {"uploaded": False}

    def delete_resume(self) -> bool:
        """Deletes resume.pdf if present."""
        if RESUME_FILE_PATH.exists():
            RESUME_FILE_PATH.unlink()
            return True
        return False


resume_storage = ResumeStorage()
