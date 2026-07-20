import os
import shutil
from pathlib import Path
from typing import Any, BinaryIO, Dict, Union


STORAGE_DIR = Path(
    os.getenv(
        "RESUME_STORAGE_DIR",
        "/tmp/smarthunt/resumes",
    )
)

RESUME_FILE_PATH = STORAGE_DIR / "resume.pdf"


class ResumeStorage:
    """
    Resume file storage manager.
    Handles saving, retrieving and deleting resume files.
    """

    def __init__(self) -> None:
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        STORAGE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save_resume(
        self,
        file_obj: Union[BinaryIO, bytes],
        filename: str,
    ) -> Dict[str, Any]:

        self._ensure_storage_dir()

        safe_filename = Path(filename).name

        file_path = STORAGE_DIR / safe_filename

        if isinstance(file_obj, bytes):

            file_path.write_bytes(
                file_obj
            )

        else:

            if hasattr(file_obj, "seek"):
                file_obj.seek(0)

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(
                    file_obj,
                    buffer,
                )

        return {
            "filename": safe_filename,
            "stored_path": str(file_path),
            "size": file_path.stat().st_size,
        }

    def get_resume_path(
        self,
        filename: str,
    ) -> Path | None:

        path = STORAGE_DIR / filename

        if path.exists():
            return path

        return None

    def get_resume_info(
        self,
    ) -> Dict[str, Any]:

        files = list(
            STORAGE_DIR.iterdir()
        )

        if not files:
            return {
                "uploaded": False
            }

        latest = files[0]

        return {
            "uploaded": True,
            "filename": latest.name,
            "stored_path": str(latest),
            "size": latest.stat().st_size,
        }

    def delete_resume(
        self,
        filename: str | None = None,
    ) -> bool:

        if filename:

            path = STORAGE_DIR / filename

            if path.exists():
                path.unlink()
                return True

            return False

        deleted = False

        for file in STORAGE_DIR.iterdir():

            if file.is_file():
                file.unlink()
                deleted = True

        return deleted


resume_storage = ResumeStorage()
