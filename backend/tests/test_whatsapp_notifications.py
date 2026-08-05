import pytest
from unittest.mock import AsyncMock
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.core.config import settings
from smarthunt.notifications.channels.whatsapp import send_whatsapp_message
from smarthunt.notifications.models import Notification


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Notification))
    await db_session.commit()


@pytest.mark.asyncio
async def test_send_whatsapp_message_noop_without_credentials(monkeypatch):
    monkeypatch.setattr(settings, "whatsapp_api_key", None)
    monkeypatch.setattr(settings, "whatsapp_api_url", None)
    monkeypatch.setattr(settings, "whatsapp_recipient_number", None)

    sent = await send_whatsapp_message("hello")

    assert sent is False


@pytest.mark.asyncio
async def test_send_whatsapp_message_posts_to_360dialog_api(monkeypatch):
    monkeypatch.setattr(settings, "whatsapp_api_key", "test-api-key")
    monkeypatch.setattr(
        settings, "whatsapp_api_url", "https://waba-sandbox.360dialog.io/v1/messages"
    )
    monkeypatch.setattr(settings, "whatsapp_recipient_number", "201011878755")

    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            pass

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers, json):
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(
        "smarthunt.notifications.channels.whatsapp.httpx.AsyncClient",
        lambda timeout=10: FakeClient(),
    )

    sent = await send_whatsapp_message("test message")

    assert sent is True
    assert captured["url"] == "https://waba-sandbox.360dialog.io/v1/messages"
    assert captured["headers"] == {
        "Content-Type": "application/json",
        "D360-API-KEY": "test-api-key",
    }
    assert captured["json"] == {
        "messaging_product": "whatsapp",
        "to": "201011878755",
        "type": "text",
        "text": {"body": "test message"},
    }


@pytest.mark.asyncio
async def test_send_whatsapp_message_never_raises_on_failure(monkeypatch):
    monkeypatch.setattr(settings, "whatsapp_api_key", "test-api-key")
    monkeypatch.setattr(
        settings, "whatsapp_api_url", "https://waba-sandbox.360dialog.io/v1/messages"
    )
    monkeypatch.setattr(settings, "whatsapp_recipient_number", "201011878755")

    class FailingClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, headers, json):
            raise RuntimeError("network error")

    monkeypatch.setattr(
        "smarthunt.notifications.channels.whatsapp.httpx.AsyncClient",
        lambda timeout=10: FailingClient(),
    )

    sent = await send_whatsapp_message("test message")

    assert sent is False


@pytest.mark.asyncio
async def test_creating_whatsapp_channel_notification_attempts_delivery(client, monkeypatch):
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr("smarthunt.notifications.service.send_whatsapp_message", mock_send)

    response = await client.post(
        "/api/v1/notifications",
        json={
            "title": "تقديم تلقائي",
            "message": "تم التقديم على وظيفة Backend Engineer في Acme",
            "type": "APPLICATION_SUBMITTED",
            "channel": "WHATSAPP",
        },
    )

    assert response.status_code == 201
    mock_send.assert_awaited_once()
    assert "تقديم تلقائي" in mock_send.call_args.args[0]


@pytest.mark.asyncio
async def test_creating_in_app_notification_does_not_attempt_whatsapp(client, monkeypatch):
    mock_send = AsyncMock(return_value=True)
    monkeypatch.setattr("smarthunt.notifications.service.send_whatsapp_message", mock_send)

    response = await client.post(
        "/api/v1/notifications",
        json={"title": "info", "message": "just fyi", "type": "INFO"},
    )

    assert response.status_code == 201
    mock_send.assert_not_awaited()
