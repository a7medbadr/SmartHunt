from io import BytesIO
from typing import Union
from fastapi import HTTPException, status
from pypdf import PdfReader
from pypdf.errors import PdfStreamError


def extract_text(source: Union[str, bytes, BytesIO]) -> str:
    """Extract raw text from a PDF file given its path, raw bytes, or BytesIO object."""
    if isinstance(source, bytes):
        source = BytesIO(source)

    try:
        reader = PdfReader(source)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text.strip()
    except (PdfStreamError, Exception) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse PDF file (invalid or corrupted file format): {str(e)}",
        )
