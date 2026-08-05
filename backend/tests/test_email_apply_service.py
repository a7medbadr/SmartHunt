from unittest.mock import AsyncMock

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.ai.types import AIProvider, AIResponse
from smarthunt.database.models.application import Application
from smarthunt.email_apply import service
from smarthunt.email_apply.models import EmailMessage
from smarthunt.notifications.models import Notification


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(EmailMessage))
    await db_session.execute(delete(Notification))
    await db_session.execute(delete(Application))
    await db_session.commit()


@pytest.fixture
async def test_application(db_session: AsyncSession) -> Application:
    application = Application(job_title="Linux Engineer", company="Acme", status="Applied")
    db_session.add(application)
    await db_session.commit()
    await db_session.refresh(application)
    return application


@pytest.mark.asyncio
async def test_draft_application_email_uses_ai_body_and_computed_subject(monkeypatch):
    """Regression test: the subject used to be parsed out of a
    "SUBJECT: <one line subject>" template slot in the AI's own output —
    confirmed live 2026-08-03 that the small local model sometimes
    echoes that placeholder text back verbatim instead of replacing it
    ("<one line subject>" landing as the literal subject). The subject
    is now always computed programmatically; only the body comes from
    the AI."""
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

    draft = await service.draft_application_email(
        resume_text="Experienced Linux engineer",
        job_title="Linux Engineer",
        company="Acme",
        job_description="Needs Linux skills",
        matched_skills=["linux"],
    )

    assert draft["subject"] == "Application for Linux Engineer"
    assert "Dear team" in draft["body"]


@pytest.mark.asyncio
async def test_draft_application_email_falls_back_when_ai_unavailable(monkeypatch):
    monkeypatch.setattr(
        service.ai_service,
        "generate",
        AsyncMock(
            return_value=AIResponse(
                content="[LOCAL LLM] echoed prompt", provider=AIProvider.LOCAL, success=True
            )
        ),
    )

    draft = await service.draft_application_email(
        resume_text="Experienced Linux engineer",
        job_title="Linux Engineer",
        company="Acme",
        job_description="Needs Linux skills",
        matched_skills=["linux"],
    )

    assert "[LOCAL LLM]" not in draft["body"]
    assert "Linux Engineer" in draft["subject"]
    assert "linux" in draft["body"].lower()


@pytest.mark.asyncio
async def test_send_application_email_creates_real_record(
    db_session: AsyncSession, test_application: Application, monkeypatch
):
    monkeypatch.setattr(service.settings, "smtp_host", "smtp.gmail.com")
    monkeypatch.setattr(service.settings, "smtp_username", "me@gmail.com")
    monkeypatch.setattr(service.settings, "smtp_password", "app-password")
    monkeypatch.setattr(service.settings, "smtp_from_email", "me@gmail.com")

    mock_send = AsyncMock()
    monkeypatch.setattr(service.aiosmtplib, "send", mock_send)

    message = await service.send_application_email(
        db_session,
        test_application.id,
        "hr@acme.com",
        "Application for Linux Engineer",
        "Dear team, please find my application attached.",
    )
    await db_session.commit()

    mock_send.assert_awaited_once()
    assert message.direction == "outbound"
    assert message.to_address == "hr@acme.com"
    assert message.message_id.strip()
    assert message.in_reply_to is None

    stored = await db_session.execute(
        select(EmailMessage).where(EmailMessage.application_id == test_application.id)
    )
    rows = stored.scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_send_application_email_requires_smtp_configured(
    db_session: AsyncSession, test_application: Application, monkeypatch
):
    monkeypatch.setattr(service.settings, "smtp_host", None)

    with pytest.raises(RuntimeError):
        await service.send_application_email(
            db_session, test_application.id, "hr@acme.com", "Subject", "Body"
        )


@pytest.mark.asyncio
async def test_check_for_replies_creates_inbound_message_and_notifies(
    db_session: AsyncSession, test_application: Application, monkeypatch
):
    outbound = EmailMessage(
        application_id=test_application.id,
        direction="outbound",
        from_address="me@gmail.com",
        to_address="hr@acme.com",
        subject="Application for Linux Engineer",
        body="Dear team...",
        message_id="<outbound-abc@smarthunt>",
        read_by_owner=True,
    )
    db_session.add(outbound)
    await db_session.commit()

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(
        service,
        "_poll_imap_sync",
        lambda message_ids: [
            {
                "from_address": "hr@acme.com",
                "subject": "Re: Application for Linux Engineer",
                "body": "Thanks for applying, can you share your notice period?",
                "message_id": "<inbound-xyz@acme>",
                "in_reply_to": "<outbound-abc@smarthunt>",
            }
        ],
    )
    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)

    notify_mock = AsyncMock()
    monkeypatch.setattr(service.notification_service, "create", notify_mock)

    created = await service.check_for_replies(db_session)
    await db_session.commit()

    assert len(created) == 1
    assert created[0].direction == "inbound"
    assert created[0].from_address == "hr@acme.com"
    assert created[0].in_reply_to == "<outbound-abc@smarthunt>"
    assert notify_mock.await_count == 2  # TELEGRAM + WHATSAPP

    channels = [call.args[1].channel for call in notify_mock.await_args_list]
    assert sorted(channels) == ["TELEGRAM", "WHATSAPP"]


@pytest.mark.asyncio
async def test_check_for_replies_skips_already_seen_messages(
    db_session: AsyncSession, test_application: Application, monkeypatch
):
    outbound = EmailMessage(
        application_id=test_application.id,
        direction="outbound",
        from_address="me@gmail.com",
        to_address="hr@acme.com",
        subject="Application",
        body="...",
        message_id="<outbound-1@smarthunt>",
        read_by_owner=True,
    )
    inbound = EmailMessage(
        application_id=test_application.id,
        direction="inbound",
        from_address="hr@acme.com",
        to_address="me@gmail.com",
        subject="Re: Application",
        body="already recorded",
        message_id="<inbound-1@acme>",
        in_reply_to="<outbound-1@smarthunt>",
        read_by_owner=False,
    )
    db_session.add_all([outbound, inbound])
    await db_session.commit()

    async def fake_to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(
        service,
        "_poll_imap_sync",
        lambda message_ids: [
            {
                "from_address": "hr@acme.com",
                "subject": "Re: Application",
                "body": "already recorded",
                "message_id": "<inbound-1@acme>",
                "in_reply_to": "<outbound-1@smarthunt>",
            }
        ],
    )
    monkeypatch.setattr("asyncio.to_thread", fake_to_thread)

    created = await service.check_for_replies(db_session)

    assert created == []


@pytest.mark.asyncio
async def test_draft_reply_uses_incoming_message_context(monkeypatch):
    monkeypatch.setattr(
        service.ai_service,
        "generate",
        AsyncMock(
            return_value=AIResponse(
                content="My notice period is 30 days.", provider=AIProvider.OLLAMA, success=True
            )
        ),
    )

    reply = await service.draft_reply("Experienced Linux engineer", "What is your notice period?")

    assert reply == "My notice period is 30 days."


@pytest.mark.asyncio
async def test_draft_reply_returns_empty_on_local_fallback(monkeypatch):
    monkeypatch.setattr(
        service.ai_service,
        "generate",
        AsyncMock(
            return_value=AIResponse(
                content="[LOCAL LLM] echo", provider=AIProvider.LOCAL, success=True
            )
        ),
    )

    reply = await service.draft_reply("resume text", "their message")

    assert reply == ""
