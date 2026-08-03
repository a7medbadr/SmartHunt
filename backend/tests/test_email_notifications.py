import pytest
from unittest.mock import AsyncMock
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.core.config import settings
from smarthunt.notifications.channels.email import send_email_message
from smarthunt.notifications.models import Notification


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Notification))
    await db_session.commit()


def _configure_smtp(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_port", 587)
    monkeypatch.setattr(settings, "smtp_username", "bot@example.com")
    monkeypatch.setattr(settings, "smtp_password", "app-password")
    monkeypatch.setattr(settings, "smtp_from_email", "bot@example.com")
    monkeypatch.setattr(settings, "notification_email", "owner@example.com")


@pytest.mark.asyncio
async def test_send_email_message_noop_without_credentials(monkeypatch):
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "notification_email", None)

    sent = await send_email_message("subject", "body")

    assert sent is False


@pytest.mark.asyncio
async def test_send_email_message_sends_via_smtp(monkeypatch):
    _configure_smtp(monkeypatch)

    mock_send = AsyncMock(return_value=None)
    monkeypatch.setattr("smarthunt.notifications.channels.email.aiosmtplib.send", mock_send)

    sent = await send_email_message("تم التقديم", "التفاصيل هنا")

    assert sent is True
    mock_send.assert_awaited_once()
    message = mock_send.call_args.args[0]
    assert message["Subject"] == "تم التقديم"
    assert message["To"] == "owner@example.com"
    assert message["From"] == "bot@example.com"
    assert mock_send.call_args.kwargs["hostname"] == "smtp.example.com"


@pytest.mark.asyncio
async def test_send_email_message_never_raises_on_failure(monkeypatch):
    _configure_smtp(monkeypatch)

    mock_send = AsyncMock(side_effect=RuntimeError("smtp connection refused"))
    monkeypatch.setattr("smarthunt.notifications.channels.email.aiosmtplib.send", mock_send)

    sent = await send_email_message("subject", "body")

    assert sent is False


@pytest.mark.asyncio
async def test_creating_email_channel_notification_attempts_delivery(client, monkeypatch):
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr("smarthunt.notifications.service.send_email_message", mock_send)

    response = await client.post(
        "/api/v1/notifications",
        json={
            "title": "تقديم تلقائي",
            "message": "تم التقديم على وظيفة Backend Engineer في Acme",
            "type": "APPLICATION_SUBMITTED",
            "channel": "EMAIL",
        },
    )

    assert response.status_code == 201
    mock_send.assert_awaited_once_with(
        "تقديم تلقائي", "تم التقديم على وظيفة Backend Engineer في Acme"
    )
