from fastapi.testclient import TestClient
from smarthunt.main import app
from smarthunt.matching.services.matcher import match
from smarthunt.matching.services.deep_analysis import _truncate_for_ai

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


def test_matcher_scores_storage_backup_job_against_infra_resume():
    """Regression test: a real job like "Storage Backup Engineer" (Veeam,
    storage administration, no python/kubernetes/terraform/jenkins at all)
    used to score a flat 0% because SKILLS only covered a generic DevOps
    set with no overlap for this domain — extract_skills() found zero
    job_skills, and match() treats that as an automatic 0 regardless of
    resume content."""
    resume = (
        "Senior Linux System Administrator with SAN/NAS storage, Veeam and NetBackup experience."
    )
    job = "Storage Backup Engineer: manage Veeam Backup & Replication and Dell EMC/NetApp storage administration."

    result = match(resume, job)
    assert result["score"] > 0
    assert "veeam" in result["matched_skills"]
    assert "storage" in result["matched_skills"]


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


def test_deep_analysis_endpoint():
    payload = {
        "resume": "Experienced in Linux and Docker",
        "job": "Needs Linux, Docker, Terraform, and AWS",
    }
    response = client.post("/api/v1/matching/deep-analysis", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["score"] == 50
    assert isinstance(data["ai_summary"], str)
    assert len(data["ai_summary"]) > 0
    assert data["provider"] in ("local", "ollama")


def test_deep_analysis_requires_both_fields():
    response = client.post("/api/v1/matching/deep-analysis", json={"resume": "", "job": "x"})
    assert response.status_code == 400


def test_truncate_for_ai_leaves_short_text_untouched():
    text = "Experienced Linux engineer with Docker and Terraform."
    assert _truncate_for_ai(text) == text


def test_truncate_for_ai_shortens_long_resume_text():
    text = "a" * 5000
    truncated = _truncate_for_ai(text)
    assert len(truncated) < len(text)
    assert truncated.startswith("a" * 1500)
