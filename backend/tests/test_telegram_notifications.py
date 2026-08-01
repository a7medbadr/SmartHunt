import pytest
from unittest.mock import AsyncMock
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.core.config import settings
from smarthunt.notifications.channels.telegram import send_telegram_message
from smarthunt.notifications.models import Notification


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Notification))
    await db_session.commit()


@pytest.mark.asyncio
async def test_send_telegram_message_noop_without_credentials(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", None)
    monkeypatch.setattr(settings, "telegram_chat_id", None)

    sent = await send_telegram_message("hello")

    assert sent is False


@pytest.mark.asyncio
async def test_send_telegram_message_posts_to_bot_api(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "test-token")
    monkeypatch.setattr(settings, "telegram_chat_id", "12345")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(
        "smarthunt.notifications.channels.telegram.httpx.AsyncClient",
        lambda timeout=10: FakeClient(),
    )

    sent = await send_telegram_message("test message")

    assert sent is True
    assert captured["url"] == "https://api.telegram.org/bottest-token/sendMessage"
    assert captured["json"] == {"chat_id": "12345", "text": "test message"}


@pytest.mark.asyncio
async def test_send_telegram_message_never_raises_on_failure(monkeypatch):
    monkeypatch.setattr(settings, "telegram_bot_token", "test-token")
    monkeypatch.setattr(settings, "telegram_chat_id", "12345")

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json):
            raise RuntimeError("network error")

    monkeypatch.setattr(
        "smarthunt.notifications.channels.telegram.httpx.AsyncClient",
        lambda timeout=10: FailingClient(),
    )

    sent = await send_telegram_message("test message")

    assert sent is False


@pytest.mark.asyncio
async def test_creating_telegram_channel_notification_attempts_delivery(client, monkeypatch):
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr("smarthunt.notifications.service.send_telegram_message", mock_send)

    response = await client.post(
        "/api/v1/notifications",
        json={
            "title": "تقديم تلقائي",
            "message": "تم التقديم على وظيفة Backend Engineer في Acme",
            "type": "APPLICATION_SUBMITTED",
            "channel": "TELEGRAM",
        },
    )

    assert response.status_code == 201
    mock_send.assert_awaited_once()
    assert "تقديم تلقائي" in mock_send.call_args.args[0]


@pytest.mark.asyncio
async def test_creating_in_app_notification_does_not_attempt_telegram(client, monkeypatch):
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr("smarthunt.notifications.service.send_telegram_message", mock_send)

    response = await client.post(
        "/api/v1/notifications",
        json={"title": "info", "message": "just fyi", "type": "INFO"},
    )

    assert response.status_code == 201
    mock_send.assert_not_awaited()
