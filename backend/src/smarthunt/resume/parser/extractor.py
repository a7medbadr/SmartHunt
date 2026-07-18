from io import BytesIO
from typing import Union
from pypdf import PdfReader


def extract_text(source: Union[str, bytes, BytesIO]) -> str:
    """Extract raw text from a PDF file given its path, raw bytes, or BytesIO object."""
    if isinstance(source, bytes):
        source = BytesIO(source)
    reader = PdfReader(source)
    return "\n".join(page.extract_text() or "" for page in reader.pages)
