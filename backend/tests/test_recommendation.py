from fastapi.testclient import TestClient
from smarthunt.main import app

client = TestClient(app)

def test_recommend_jobs():
    response = client.post(
        "/api/v1/jobs/recommend",
        json={"resume": "Linux Docker Python OpenShift AWS"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0
    assert "title" in data["recommendations"][0]
    assert "score" in data["recommendations"][0]
