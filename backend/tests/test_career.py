from fastapi.testclient import TestClient
from smarthunt.main import app

client = TestClient(app)


def test_career_advice():
    response = client.post(
        "/api/v1/career/advice",
        json={"resume": "Linux Docker Python"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "current_level" in data
    assert "recommended_roles" in data
    assert "skills_to_learn" in data
    assert "next_certifications" in data
