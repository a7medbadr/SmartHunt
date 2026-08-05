import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock

from smarthunt.ai.types import AIProvider, AIResponse
from smarthunt.database.models.job import Job
from smarthunt.database.models.resume import Resume
from smarthunt.database.models.user import User
from smarthunt.resume.models import TailoredResume
from smarthunt.resume.services.tailoring import generate_tailored_resume, get_tailored_resume


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(TailoredResume))
    await db_session.execute(delete(Job))
    await db_session.execute(delete(Resume))
    await db_session.execute(delete(User).where(User.username.like("tailoring_test_user_%")))
    await db_session.commit()


@pytest.fixture
async def test_job(db_session: AsyncSession) -> int:
    job = Job(
        title="Linux Engineer",
        company="Acme",
        location="Riyadh",
        description="Needs Linux, Docker, Terraform, and AWS",
        requirements="Linux, Docker",
        source="test",
        url="http://example.com/job/tailoring/1",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job.id


@pytest.fixture
async def test_resume(db_session: AsyncSession) -> str:
    uid = uuid.uuid4().hex[:8]
    user = User(
        username=f"tailoring_test_user_{uid}",
        email=f"tailoring_test_user_{uid}@example.com",
        password_hash="not-a-real-hash",
    )
    db_session.add(user)
    await db_session.flush()

    resume = Resume(
        user_id=user.id,
        filename="cv.pdf",
        stored_path="/tmp/does-not-matter.pdf",
        extracted_text="Experienced in Linux and Docker",
    )
    db_session.add(resume)
    await db_session.commit()
    return resume.extracted_text


@pytest.mark.asyncio
async def test_generate_tailored_resume_keeps_original_text_verbatim(
    db_session: AsyncSession, test_job: int, monkeypatch
):
    """The tiny local model is only trusted to write a short summary, not
    rewrite factual resume content — the real resume text must survive
    untouched in the composed output, to avoid it hallucinating dates,
    companies, or achievements on a document used for real applications."""
    monkeypatch.setattr(
        "smarthunt.resume.services.tailoring.ai_service.generate",
        AsyncMock(
            return_value=AIResponse(
                content="Tailored summary for this exact role.",
                provider=AIProvider.OLLAMA,
                success=True,
            )
        ),
    )

    resume_text = "Experienced in Linux and Docker\nAcme Corp, 2020-2024"

    tailored = await generate_tailored_resume(
        db_session,
        job_id=test_job,
        resume_text=resume_text,
        job_description="Needs Linux, Docker, Terraform, and AWS",
    )

    assert resume_text in tailored.generated_text
    assert "Tailored summary for this exact role." in tailored.generated_text
    assert tailored.matched_skills == ["docker", "linux"]
    assert tailored.missing_skills == ["aws", "terraform"]
    assert tailored.score == 50
    assert tailored.file_path.endswith(f"{test_job}.docx")

    from pathlib import Path

    assert Path(tailored.file_path).exists()


@pytest.mark.asyncio
async def test_generate_tailored_resume_falls_back_when_ai_unavailable(
    db_session: AsyncSession, test_job: int, monkeypatch
):
    """A LOCAL-provider fallback (or an outright exception) must not
    surface the fake echo stub as if it were a real tailored summary —
    same rule as cover_letter/service.py and matching/deep_analysis.py."""
    monkeypatch.setattr(
        "smarthunt.resume.services.tailoring.ai_service.generate",
        AsyncMock(
            return_value=AIResponse(
                content="[LOCAL LLM] echoed prompt back",
                provider=AIProvider.LOCAL,
                success=True,
            )
        ),
    )

    tailored = await generate_tailored_resume(
        db_session,
        job_id=test_job,
        resume_text="Experienced in Linux and Docker",
        job_description="Needs Linux and Docker",
    )

    assert "[LOCAL LLM]" not in tailored.summary
    assert "linux" in tailored.summary.lower() or "docker" in tailored.summary.lower()


@pytest.mark.asyncio
async def test_generate_tailored_resume_upserts_on_regeneration(
    db_session: AsyncSession, test_job: int, monkeypatch
):
    monkeypatch.setattr(
        "smarthunt.resume.services.tailoring.ai_service.generate",
        AsyncMock(
            return_value=AIResponse(content="v1 summary", provider=AIProvider.OLLAMA, success=True)
        ),
    )

    first = await generate_tailored_resume(
        db_session, job_id=test_job, resume_text="Linux", job_description="Linux"
    )

    monkeypatch.setattr(
        "smarthunt.resume.services.tailoring.ai_service.generate",
        AsyncMock(
            return_value=AIResponse(content="v2 summary", provider=AIProvider.OLLAMA, success=True)
        ),
    )

    second = await generate_tailored_resume(
        db_session, job_id=test_job, resume_text="Linux", job_description="Linux"
    )

    assert first.id == second.id
    assert second.summary == "v2 summary"

    fetched = await get_tailored_resume(db_session, test_job)
    assert fetched.summary == "v2 summary"


@pytest.mark.asyncio
async def test_tailored_resume_endpoint_requires_uploaded_resume(
    client: AsyncClient, db_session: AsyncSession, test_job: int
):
    # A resume row can be left over from other test files' fixtures in
    # this shared test database — clear it first so this test genuinely
    # exercises the "nothing uploaded yet" path rather than depending on
    # accidental ordering.
    await db_session.execute(delete(Resume))
    await db_session.commit()

    response = await client.post(f"/api/v1/resume/tailored/{test_job}")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_tailored_resume_endpoint_requires_existing_job(client: AsyncClient, test_resume):
    response = await client.post("/api/v1/resume/tailored/9999999")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tailored_resume_endpoint_generates_and_fetches(
    client: AsyncClient, test_job: int, test_resume, monkeypatch
):
    monkeypatch.setattr(
        "smarthunt.resume.services.tailoring.ai_service.generate",
        AsyncMock(
            return_value=AIResponse(
                content="Tailored summary.", provider=AIProvider.OLLAMA, success=True
            )
        ),
    )

    response = await client.post(f"/api/v1/resume/tailored/{test_job}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == test_job
    assert data["score"] == 50
    assert "Tailored summary." in data["generated_text"]

    fetch = await client.get(f"/api/v1/resume/tailored/{test_job}")
    assert fetch.status_code == 200
    assert fetch.json()["job_id"] == test_job


@pytest.mark.asyncio
async def test_tailored_resume_endpoint_404_when_not_generated_yet(
    client: AsyncClient, test_job: int
):
    response = await client.get(f"/api/v1/resume/tailored/{test_job}")

    assert response.status_code == 404
