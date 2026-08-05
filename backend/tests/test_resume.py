import io
import uuid

import pytest
from docx import Document
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, StreamObject

from smarthunt.database.models.resume import Resume


def _make_valid_pdf_bytes() -> bytes:
    """A real, minimal, pypdf-extractable PDF — resume/api/router.py's
    upload endpoint now rejects uploads whose extracted text is empty/too
    short (found 2026-08-04: a scanned-PDF upload with 0 extractable
    chars used to silently delete the user's existing working resume and
    replace it with this useless one), so tests need a file that
    actually round-trips real text through pypdf, not arbitrary bytes
    with a `%PDF` prefix."""
    writer = PdfWriter()
    page = writer.add_blank_page(width=612, height=792)

    content = (
        b"BT /F1 12 Tf 72 712 Td "
        b"(Experienced Software Engineer with Python and Linux skills for testing.) Tj ET"
    )
    stream_obj = StreamObject()
    stream_obj.set_data(content)
    stream_ref = writer._add_object(stream_obj)

    font_ref = writer._add_object(
        DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
    )

    page[NameObject("/Contents")] = stream_ref
    page[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
    )

    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


async def _auth_headers(client) -> dict:
    uid = uuid.uuid4().hex[:8]
    payload = {
        "username": f"resume_user_{uid}",
        "email": f"{uid}@example.com",
        "password": "Secret123",
    }
    await client.post("/api/v1/auth/register", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"username": payload["username"], "password": payload["password"]},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_resume_lifecycle(tmp_path, monkeypatch, client):
    # Patch STORAGE_DIR to use temporary directory during test
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)
    monkeypatch.setattr(
        "smarthunt.resume.storage.storage.RESUME_FILE_PATH", storage_dir / "resume.pdf"
    )

    headers = await _auth_headers(client)

    # 1. GET resume when empty
    response = await client.get("/api/v1/resume", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"uploaded": False}

    # 2. Upload invalid file extension (.txt)
    invalid_file = ("test.txt", io.BytesIO(b"dummy text"), "text/plain")
    response = await client.post(
        "/api/v1/resume/upload", files={"file": invalid_file}, headers=headers
    )
    assert response.status_code == 400

    # 3. Upload valid PDF file
    pdf_content = _make_valid_pdf_bytes()
    valid_file = ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await client.post(
        "/api/v1/resume/upload", files={"file": valid_file}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == "uploaded"
    assert response.json()["size"] == len(pdf_content)

    # 4. GET resume after upload
    response = await client.get("/api/v1/resume", headers=headers)
    assert response.status_code == 200
    assert response.json()["uploaded"] is True
    assert response.json()["filename"] == "resume.pdf"

    # 5. DELETE resume
    response = await client.delete("/api/v1/resume", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}

    # 6. GET resume after deletion
    response = await client.get("/api/v1/resume", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"uploaded": False}


@pytest.mark.asyncio
async def test_resume_upload_logs_activity(tmp_path, monkeypatch, client):
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)
    monkeypatch.setattr(
        "smarthunt.resume.storage.storage.RESUME_FILE_PATH", storage_dir / "resume.pdf"
    )

    headers = await _auth_headers(client)

    pdf_content = _make_valid_pdf_bytes()
    valid_file = ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await client.post(
        "/api/v1/resume/upload", files={"file": valid_file}, headers=headers
    )
    assert response.status_code == 200

    # GET /activity is capped at 20 most-recent rows, so on a long-lived
    # shared DB a raw count comparison isn't reliable — just check the
    # newest entry (index 0, ordered by created_at desc) is this upload.
    after = await client.get("/api/v1/activity")
    assert after.json()[0]["type"] == "resume_uploaded"


@pytest.mark.asyncio
async def test_resume_upload_requires_auth(tmp_path, monkeypatch, client):
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)
    monkeypatch.setattr(
        "smarthunt.resume.storage.storage.RESUME_FILE_PATH", storage_dir / "resume.pdf"
    )

    pdf_content = _make_valid_pdf_bytes()
    valid_file = ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await client.post("/api/v1/resume/upload", files={"file": valid_file})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_resume_upload_persists_to_database_as_canonical_reference(
    tmp_path, monkeypatch, client, db_session
):
    """The whole point: an uploaded resume becomes the DB-backed reference
    everything else (search score, cover letter, matching) reads from —
    not just a file sitting on disk that nothing else touches."""
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)
    monkeypatch.setattr(
        "smarthunt.resume.storage.storage.RESUME_FILE_PATH", storage_dir / "resume.pdf"
    )

    headers = await _auth_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    pdf_content = _make_valid_pdf_bytes()
    valid_file = ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await client.post(
        "/api/v1/resume/upload", files={"file": valid_file}, headers=headers
    )
    assert response.status_code == 200

    rows = (await db_session.execute(Resume.__table__.select())).all()
    matching = [r for r in rows if r.user_id == user_id]
    assert len(matching) == 1
    assert matching[0].filename == "resume.pdf"

    # Uploading again replaces the row rather than accumulating history —
    # there's exactly one canonical resume at a time.
    response = await client.post(
        "/api/v1/resume/upload", files={"file": valid_file}, headers=headers
    )
    assert response.status_code == 200

    rows_after = (await db_session.execute(Resume.__table__.select())).all()
    matching_after = [r for r in rows_after if r.user_id == user_id]
    assert len(matching_after) == 1


@pytest.mark.asyncio
async def test_resume_upload_rejects_unreadable_pdf_without_deleting_existing_one(
    tmp_path, monkeypatch, client, db_session
):
    """Regression test: a scanned/image-only PDF (or any file pypdf can't
    extract real text from) used to still be accepted with a 200 — the
    upload handler deleted the user's existing, working resume *before*
    checking whether the new file's extraction actually produced
    anything, silently replacing a good resume with a useless one (found
    2026-08-04 live: every match score/AI feature reads "whichever
    resume is most recent", so this broke everything downstream with no
    visible error). The upload must be rejected instead, and the
    existing resume must survive untouched."""
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)
    monkeypatch.setattr(
        "smarthunt.resume.storage.storage.RESUME_FILE_PATH", storage_dir / "resume.pdf"
    )

    headers = await _auth_headers(client)

    good_file = ("real_resume.pdf", io.BytesIO(_make_valid_pdf_bytes()), "application/pdf")
    good_response = await client.post(
        "/api/v1/resume/upload", files={"file": good_file}, headers=headers
    )
    assert good_response.status_code == 200

    # A syntactically-valid-enough PDF that pypdf can open but has no
    # extractable text at all (no content stream, no font/text objects) —
    # simulates a scanned/image-only PDF.
    unreadable_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj\n"
        b"trailer << /Root 1 0 R >>\n"
        b"%%EOF"
    )
    bad_file = ("scanned.pdf", io.BytesIO(unreadable_pdf), "application/pdf")
    bad_response = await client.post(
        "/api/v1/resume/upload", files={"file": bad_file}, headers=headers
    )
    assert bad_response.status_code == 400

    text_response = await client.get("/api/v1/resume/text")
    assert text_response.status_code == 200
    assert "Python" in text_response.json()["text"]


@pytest.mark.asyncio
async def test_get_resume_survives_ephemeral_storage_being_wiped(tmp_path, monkeypatch, client):
    """Regression test: GET /resume used to read resume_service.get_resume(),
    which just lists files in the local STORAGE_DIR — a directory that
    lives inside the container and is wiped on every restart/redeploy.
    The DB row (written by upload) is the durable source of truth; GET
    must read that, not the ephemeral directory listing, so the Resume
    page doesn't falsely report "nothing uploaded" after a routine
    backend restart."""
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)
    monkeypatch.setattr(
        "smarthunt.resume.storage.storage.RESUME_FILE_PATH", storage_dir / "resume.pdf"
    )

    headers = await _auth_headers(client)

    pdf_content = _make_valid_pdf_bytes()
    valid_file = ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = await client.post(
        "/api/v1/resume/upload", files={"file": valid_file}, headers=headers
    )
    assert response.status_code == 200

    # Simulate a container restart wiping the ephemeral storage directory —
    # the DB row must still be found.
    for f in storage_dir.iterdir():
        f.unlink()

    response = await client.get("/api/v1/resume", headers=headers)
    assert response.status_code == 200
    assert response.json()["uploaded"] is True
    assert response.json()["filename"] == "resume.pdf"


@pytest.mark.asyncio
async def test_get_resume_text_returns_extracted_text(tmp_path, monkeypatch, client):
    """Other features (cover letter, AI assistant) read the resume via
    this endpoint instead of asking the user to paste it again."""
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)

    headers = await _auth_headers(client)

    # Not asserting "no resume yet returns None" here — the resumes table
    # is shared across this whole test file's real DB, so an earlier
    # test's upload may already be the most-recently-updated row.

    doc_buffer = io.BytesIO()
    doc = Document()
    doc.add_paragraph("Senior Python Engineer with 10 years of experience.")
    doc.save(doc_buffer)
    doc_buffer.seek(0)

    upload_response = await client.post(
        "/api/v1/resume/upload",
        files={
            "file": (
                "resume.docx",
                doc_buffer,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers=headers,
    )
    assert upload_response.status_code == 200

    text_response = await client.get("/api/v1/resume/text")
    assert text_response.status_code == 200
    assert "Senior Python Engineer" in text_response.json()["text"]
