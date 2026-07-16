from pathlib import Path
from uuid import uuid4

UPLOAD_DIR = Path("uploads/resumes")


def save_resume(filename: str, content: bytes) -> Path:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    extension = Path(filename).suffix.lower()

    target = UPLOAD_DIR / f"{uuid4()}{extension}"

    target.write_bytes(content)

    return target
