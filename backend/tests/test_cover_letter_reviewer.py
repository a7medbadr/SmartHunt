from fastapi.testclient import TestClient
from smarthunt.main import app

client = TestClient(app)


def test_cover_letter_review_endpoint():
    payload = {"cover_letter": "I am applying for the job."}
    response = client.post("/api/v1/cover-letter/review", json=payload)

    assert response.status_code == 200
    data = response.json()

    assert "score" in data
    assert "issues" in data
    assert "recommendations" in data
    assert isinstance(data["score"], int)
    assert isinstance(data["issues"], list)
