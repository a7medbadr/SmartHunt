from pathlib import Path

from docx import Document
from pypdf import PdfReader


def extract_text(path: Path) -> str:
    ext = path.suffix.lower()

    if ext == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".docx":
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(f"Unsupported file type: {ext}")
