from fastapi.testclient import TestClient
from smarthunt.main import app

client = TestClient(app)


def test_resume_review_endpoint():
    payload = {
        "resume": "Experienced engineer with Linux and Docker. Achieved 20% performance increase."
    }
    response = client.post("/api/v1/resume/review", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "ats_score" in data
    assert "strengths" in data
    assert "weaknesses" in data
    assert "recommendations" in data

    assert isinstance(data["ats_score"], int)
    assert "Linux" in data["strengths"]
    assert "Docker" in data["strengths"]
    assert "No AWS" in data["weaknesses"]
