import pytest
from docx import Document

from smarthunt.database.models.job import Job


@pytest.mark.asyncio
async def test_search_jobs_endpoint(client, db_session):
    """Job search hits the real database, not a hardcoded fixture list."""
    db_session.add(
        Job(
            title="Senior Backend Engineer",
            company="Acme",
            location="Remote",
            source="linkedin",
            url="https://example.com/jobs/senior-backend-engineer",
        )
    )
    await db_session.commit()

    response = await client.get("/api/v1/search/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data
    assert isinstance(data["jobs"], list)
    assert len(data["jobs"]) > 0
    assert any(job["title"] == "Senior Backend Engineer" for job in data["jobs"])


@pytest.mark.asyncio
async def test_search_score_reflects_real_resume_match(tmp_path, monkeypatch, client, db_session):
    """score_min/sort=score used to be accepted but silently ignored (no
    salary/score data existed anywhere). They now reflect a real match
    against the uploaded resume's text."""
    storage_dir = tmp_path / "resumes"
    storage_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("smarthunt.resume.storage.storage.STORAGE_DIR", storage_dir)

    doc = Document()
    doc.add_paragraph("Experienced Python and Docker engineer.")
    doc.save(storage_dir / "resume.docx")

    db_session.add_all(
        [
            Job(
                title="Score Test Python Engineer",
                company="Acme",
                location="Remote",
                source="test",
                url="https://example.com/jobs/score-test-python-engineer",
                requirements="python docker",
            ),
            Job(
                title="Score Test AIX Administrator",
                company="Acme",
                location="Remote",
                source="test",
                url="https://example.com/jobs/score-test-aix-admin",
                requirements="aix",
            ),
        ]
    )
    await db_session.commit()

    response = await client.get(
        "/api/v1/search/jobs",
        params={"sort": "score", "order": "desc", "score_min": 1, "limit": 100},
    )
    assert response.status_code == 200
    jobs = response.json()["jobs"]
    titles = [job["title"] for job in jobs]

    assert "Score Test Python Engineer" in titles
    assert "Score Test AIX Administrator" not in titles

    python_job = next(j for j in jobs if j["title"] == "Score Test Python Engineer")
    assert python_job["score"] == 100
