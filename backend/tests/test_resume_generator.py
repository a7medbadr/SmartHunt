from fastapi.testclient import TestClient
from smarthunt.main import app
from smarthunt.resume.services.generator import generate_resume

client = TestClient(app)


def test_generate_resume_service_basic():
    resume_text = "Experienced in Linux and Docker"
    job_text = "Needs Linux, Docker, Terraform, and AWS"

    result = generate_resume(resume_text, job_text)

    assert result["score"] == 50
    assert result["matched_skills"] == ["docker", "linux"]
    assert result["recommended_skills"] == ["aws", "terraform"]
    assert "Linux" in result["generated_resume"]
    assert "Docker" in result["generated_resume"]


def test_generate_resume_api_endpoint():
    payload = {
        "resume": "Linux Docker Python OpenShift",
        "job": "Linux Docker Terraform AWS",
    }
    response = client.post("/api/v1/resume/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 50
    assert data["matched_skills"] == ["docker", "linux"]
    assert data["recommended_skills"] == ["aws", "terraform"]
    assert "generated_resume" in data
    assert "# Tailored Professional Resume" in data["generated_resume"]


def test_generate_resume_empty_job():
    payload = {
        "resume": "Linux Python",
        "job": "No technical skills required",
    }
    response = client.post("/api/v1/resume/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 0
    assert data["matched_skills"] == []
    assert data["recommended_skills"] == []
    assert "generated_resume" in data


def test_generate_resume_empty_resume():
    payload = {
        "resume": "",
        "job": "Requires Linux and Docker",
    }
    response = client.post("/api/v1/resume/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 0
    assert data["matched_skills"] == []
    assert data["recommended_skills"] == ["docker", "linux"]


def test_generate_resume_duplicate_skills():
    payload = {
        "resume": "Linux Linux Docker docker Python",
        "job": "Linux Docker Docker",
    }
    response = client.post("/api/v1/resume/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["score"] == 100
    assert data["matched_skills"] == ["docker", "linux"]
    assert data["recommended_skills"] == []
