import uuid
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.ai.types import AIProvider, AIResponse
from smarthunt.database.models.job import Job
from smarthunt.database.models.resume import Resume
from smarthunt.database.models.user import User
from smarthunt.email_apply import service
from smarthunt.email_apply.models import EmailMessage
from smarthunt.database.models.application import Application


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(EmailMessage))
    await db_session.execute(delete(Application))
    await db_session.execute(delete(Job))
    await db_session.execute(delete(Resume))
    await db_session.execute(delete(User).where(User.username.like("email_apply_test_user_%")))
    await db_session.commit()


@pytest.fixture
async def test_job_with_email(db_session: AsyncSession) -> int:
    job = Job(
        title="Linux Engineer",
        company="Acme",
        location="Riyadh",
        description="We need a Linux engineer. Send your CV to hiring@acme.com to apply.",
        requirements="Linux, Docker",
        source="test",
        url="http://example.com/job/email-apply/1",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job.id


@pytest.fixture
async def test_job_without_email(db_session: AsyncSession) -> int:
    job = Job(
        title="Linux Engineer No Email",
        company="Acme",
        location="Riyadh",
        description="Apply through our careers portal.",
        requirements="Linux",
        source="test",
        url="http://example.com/job/email-apply/2",
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job.id


@pytest.fixture
async def test_resume(db_session: AsyncSession) -> str:
    uid = uuid.uuid4().hex[:8]
    user = User(
        username=f"email_apply_test_user_{uid}",
        email=f"email_apply_test_user_{uid}@example.com",
        password_hash="not-a-real-hash",
    )
    db_session.add(user)
    await db_session.flush()

    resume = Resume(
        user_id=user.id,
        filename="cv.pdf",
        stored_path="/tmp/does-not-matter.pdf",
        extracted_text="Experienced Linux engineer with Docker skills",
    )
    db_session.add(resume)
    await db_session.commit()
    return resume.extracted_text


@pytest.mark.asyncio
async def test_draft_requires_email_in_job_description(
    client: AsyncClient, test_job_without_email: int, test_resume
):
    response = await client.post(
        "/api/v1/email-apply/draft", json={"job_id": test_job_without_email}
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_draft_requires_existing_resume(client: AsyncClient, test_job_with_email: int):
    response = await client.post("/api/v1/email-apply/draft", json={"job_id": test_job_with_email})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_draft_returns_recipient_and_content(
    client: AsyncClient, test_job_with_email: int, test_resume, monkeypatch
):
    monkeypatch.setattr(
        service.ai_service,
        "generate",
        AsyncMock(
            return_value=AIResponse(
                content="Dear team, I would like to apply.",
                provider=AIProvider.OLLAMA,
                success=True,
            )
        ),
    )

    response = await client.post("/api/v1/email-apply/draft", json={"job_id": test_job_with_email})

    assert response.status_code == 200
    data = response.json()
    assert data["recipient_email"] == "hiring@acme.com"
    assert data["subject"] == "Application for Linux Engineer"
    assert "Dear team" in data["body"]


@pytest.mark.asyncio
async def test_send_creates_application_and_thread_message(
    client: AsyncClient, db_session: AsyncSession, test_job_with_email: int, monkeypatch
):
    monkeypatch.setattr(service.settings, "smtp_host", "smtp.gmail.com")
    monkeypatch.setattr(service.settings, "smtp_username", "me@gmail.com")
    monkeypatch.setattr(service.settings, "smtp_password", "app-password")
    monkeypatch.setattr(service.settings, "smtp_from_email", "me@gmail.com")
    monkeypatch.setattr(service.aiosmtplib, "send", AsyncMock())

    response = await client.post(
        "/api/v1/email-apply/send",
        json={
            "job_id": test_job_with_email,
            "recipient_email": "hiring@acme.com",
            "subject": "Application for Linux Engineer",
            "body": "Dear team, please find my application.",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["direction"] == "outbound"
    application_id = data["application_id"]

    thread_response = await client.get(f"/api/v1/email-apply/{application_id}/thread")
    assert thread_response.status_code == 200
    thread = thread_response.json()
    assert len(thread) == 1
    assert thread[0]["subject"] == "Application for Linux Engineer"


@pytest.mark.asyncio
async def test_reply_draft_requires_an_existing_inbound_message(
    client: AsyncClient, db_session: AsyncSession
):
    application = Application(job_title="Linux Engineer", company="Acme", status="Applied")
    db_session.add(application)
    await db_session.commit()
    await db_session.refresh(application)

    response = await client.post(f"/api/v1/email-apply/{application.id}/reply/draft")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_reply_send_uses_correct_threading_headers(
    client: AsyncClient, db_session: AsyncSession, monkeypatch
):
    application = Application(job_title="Linux Engineer", company="Acme", status="Applied")
    db_session.add(application)
    await db_session.flush()

    inbound = EmailMessage(
        application_id=application.id,
        direction="inbound",
        from_address="hr@acme.com",
        to_address="me@gmail.com",
        subject="Re: Application for Linux Engineer",
        body="What is your notice period?",
        message_id="<inbound-1@acme>",
        in_reply_to="<outbound-1@smarthunt>",
        read_by_owner=False,
    )
    db_session.add(inbound)
    await db_session.commit()

    monkeypatch.setattr(service.settings, "smtp_host", "smtp.gmail.com")
    monkeypatch.setattr(service.settings, "smtp_username", "me@gmail.com")
    monkeypatch.setattr(service.settings, "smtp_password", "app-password")
    monkeypatch.setattr(service.settings, "smtp_from_email", "me@gmail.com")
    monkeypatch.setattr(service.aiosmtplib, "send", AsyncMock())

    response = await client.post(
        f"/api/v1/email-apply/{application.id}/reply/send",
        json={"body": "My notice period is 30 days."},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["to_address"] == "hr@acme.com"
    assert data["subject"] == "Re: Application for Linux Engineer"
