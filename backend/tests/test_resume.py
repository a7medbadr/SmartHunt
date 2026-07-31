import io
from fastapi.testclient import TestClient
from smarthunt.main import app

client = TestClient(app)


def test_resume_lifecycle(tmp_path, monkeypatch):
    # Patch STORAGE_DIR to use temporary directory during test
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)
    monkeypatch.setattr(
        "smarthunt.resume.storage.storage.RESUME_FILE_PATH", storage_dir / "resume.pdf"
    )

    # 1. GET resume when empty
    response = client.get("/api/v1/resume")
    assert response.status_code == 200
    assert response.json() == {"uploaded": False}

    # 2. Upload invalid file extension (.txt)
    invalid_file = ("test.txt", io.BytesIO(b"dummy text"), "text/plain")
    response = client.post("/api/v1/resume/upload", files={"file": invalid_file})
    assert response.status_code == 400

    # 3. Upload valid PDF file
    pdf_content = b"%PDF-1.4 dummy pdf content"
    valid_file = ("resume.pdf", io.BytesIO(pdf_content), "application/pdf")
    response = client.post("/api/v1/resume/upload", files={"file": valid_file})
    assert response.status_code == 200
    assert response.json()["status"] == "uploaded"
    assert response.json()["size"] == len(pdf_content)

    # 4. GET resume after upload
    response = client.get("/api/v1/resume")
    assert response.status_code == 200
    assert response.json()["uploaded"] is True
    assert response.json()["filename"] == "resume.pdf"

    # 5. DELETE resume
    response = client.delete("/api/v1/resume")
    assert response.status_code == 200
    assert response.json() == {"status": "deleted"}

    # 6. GET resume after deletion
    response = client.get("/api/v1/resume")
    assert response.status_code == 200
    assert response.json() == {"uploaded": False}
