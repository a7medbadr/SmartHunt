from fastapi.testclient import TestClient
from smarthunt.main import app

client = TestClient(app)


def test_jobs_analyze_api():
    response = client.post(
        "/api/v1/jobs/analyze",
        json={"description": "Required skills: Linux, Docker, Terraform, AWS, Kafka"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert "linux" in data["skills"]
    assert "kafka" in data["skills"]


def test_matching_analyze_api():
    payload = {
        "resume": "Linux Docker Python OpenShift C++",
        "job": "Linux Docker Terraform AWS",
    }
    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 50
    assert sorted(data["matched_skills"]) == ["docker", "linux"]
    assert sorted(data["missing_skills"]) == ["aws", "terraform"]


def test_matching_analyze_empty_job():
    payload = {
        "resume": "Linux Python",
        "job": "No technical skills listed here",
    }
    response = client.post("/api/v1/matching/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 0
    assert data["matched_skills"] == []
    assert data["missing_skills"] == []
