from fastapi.testclient import TestClient
from smarthunt.main import app
from smarthunt.matching.services.matcher import match

client = TestClient(app)


def test_matcher_full_match():
    resume = "Experienced Linux engineer with Docker, Terraform, and AWS."
    job = "Looking for Linux, Docker, Terraform, and AWS specialist."

    result = match(resume, job)
    assert result["score"] == 100
    assert sorted(result["matched_skills"]) == ["aws", "docker", "linux", "terraform"]
    assert result["missing_skills"] == []


def test_matcher_partial_match():
    resume = "Skills: Linux, Python, OpenShift, Git, Docker"
    job = "Requirements: Linux, Docker, Terraform, AWS"

    result = match(resume, job)
    assert result["score"] == 50
    assert sorted(result["matched_skills"]) == ["docker", "linux"]
    assert sorted(result["missing_skills"]) == ["aws", "terraform"]


def test_matcher_no_match_and_empty():
    # Empty resume
    result = match("", "Job requires Linux and Docker")
    assert result["score"] == 0
    assert result["matched_skills"] == []
    assert sorted(result["missing_skills"]) == ["docker", "linux"]

    # No overlapping skills
    resume = "Expert in Java and SQL"
    job = "Looking for Ansible and Kubernetes"
    result = match(resume, job)
    assert result["score"] == 0
    assert result["matched_skills"] == []
    assert sorted(result["missing_skills"]) == ["ansible", "kubernetes"]


def test_matching_api_endpoint():
    payload = {
        "resume": "Experienced in Linux and Docker",
        "job": "Needs Linux, Docker, Terraform, and AWS",
    }
    response = client.post("/api/v1/matching", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 50
    assert "linux" in data["matched_skills"]
    assert "terraform" in data["missing_skills"]
