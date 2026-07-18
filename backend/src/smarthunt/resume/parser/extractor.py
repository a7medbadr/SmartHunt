from pypdf import PdfReader


def extract_text(path: str) -> str:
    """Extract raw text from a PDF file given its path."""
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)
