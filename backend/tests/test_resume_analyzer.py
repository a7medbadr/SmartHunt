import io

from fastapi.testclient import TestClient

from smarthunt.main import app
from smarthunt.resume.parser.skills import extract_skills

client = TestClient(app)


# --- Extract Skills ---


def test_extract_skills_finds_known_skills():
    text = "I have experience with Linux, Python and Docker in production."
    skills = extract_skills(text)

    assert "linux" in skills
    assert "python" in skills
    assert "docker" in skills
    assert "kubernetes" not in skills


def test_extract_skills_no_duplicates():
    text = "Linux linux LINUX Python python"
    skills = extract_skills(text)

    assert skills.count("linux") == 1
    assert skills.count("python") == 1


def test_extract_skills_empty_text():
    assert extract_skills("") == []
    assert extract_skills(None) == []


# --- Upload PDF / API Response ---


def test_analyze_resume_rejects_non_pdf():
    invalid_file = ("resume.txt", io.BytesIO(b"Linux Python Docker"), "text/plain")
    response = client.post("/api/v1/resume/analyze", files={"file": invalid_file})

    assert response.status_code == 400


def test_analyze_resume_extracts_skills(monkeypatch):
    monkeypatch.setattr(
        "smarthunt.resume.api.router.extract_text",
        lambda path: "Looking for a candidate skilled in Linux, Python and Docker.",
    )

    pdf_file = ("resume.pdf", io.BytesIO(b"%PDF-1.4 dummy pdf content"), "application/pdf")
    response = client.post("/api/v1/resume/analyze", files={"file": pdf_file})

    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert set(data["skills"]) == {"linux", "python", "docker"}
