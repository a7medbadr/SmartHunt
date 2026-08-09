from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.whatsapp_monitor import router as router_module
from smarthunt.whatsapp_monitor.chat_scanner import WhatsAppScanError
from smarthunt.whatsapp_monitor.models import MonitoredWhatsAppChat

CHAT_URL = "https://whatsapp.com/channel/0029VbCO2TBEAKWBrwOfNU3O"
CHAT_LABEL = "ELITE IT | وظائف تقنية معلومات - السعودية"

RELEVANT_MESSAGE_TEXT = (
    "📌 Job Opportunity | Linux System Administrator\n"
    "\n"
    "🏢 Acme Systems\n"
    "\n"
    "📍 Riyadh, Saudi Arabia\n"
    "\n"
    "🌟 Requirements:\n"
    "🔹 5+ years RHEL/Linux administration experience.\n"
)


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Job).where(Job.source == "whatsapp_message"))
    await db_session.execute(delete(MonitoredWhatsAppChat))
    await db_session.commit()


@pytest.mark.asyncio
async def test_add_and_list_chat(client: AsyncClient):
    response = await client.post(
        "/api/v1/whatsapp-monitor/chats",
        json={"chat_url": CHAT_URL, "label": CHAT_LABEL, "chat_type": "channel"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["chat_url"] == CHAT_URL
    assert data["label"] == CHAT_LABEL
    assert data["chat_type"] == "channel"
    assert data["enabled"] is True

    list_response = await client.get("/api/v1/whatsapp-monitor/chats")
    assert list_response.status_code == 200
    assert any(c["id"] == data["id"] for c in list_response.json())


@pytest.mark.asyncio
async def test_update_and_delete_chat(client: AsyncClient):
    create = await client.post(
        "/api/v1/whatsapp-monitor/chats",
        json={"chat_url": CHAT_URL, "label": CHAT_LABEL, "chat_type": "channel"},
    )
    chat_id = create.json()["id"]

    update = await client.patch(
        f"/api/v1/whatsapp-monitor/chats/{chat_id}", json={"enabled": False}
    )
    assert update.status_code == 200
    assert update.json()["enabled"] is False

    delete_response = await client.delete(f"/api/v1/whatsapp-monitor/chats/{chat_id}")
    assert delete_response.status_code == 204

    missing_update = await client.patch(
        f"/api/v1/whatsapp-monitor/chats/{chat_id}", json={"enabled": True}
    )
    assert missing_update.status_code == 404


@pytest.mark.asyncio
async def test_scan_chat_saves_relevant_messages_and_marks_checked(
    client: AsyncClient, monkeypatch
):
    create = await client.post(
        "/api/v1/whatsapp-monitor/chats",
        json={"chat_url": CHAT_URL, "label": CHAT_LABEL, "chat_type": "channel"},
    )
    chat_id = create.json()["id"]

    fake_messages = [
        {"text": RELEVANT_MESSAGE_TEXT, "post_url": f"{CHAT_URL}#msg-1"},
    ]
    monkeypatch.setattr(router_module, "scan_chat", AsyncMock(return_value=fake_messages))

    response = await client.post(f"/api/v1/whatsapp-monitor/chats/{chat_id}/scan")

    assert response.status_code == 200
    data = response.json()
    assert data["scanned"] == 1
    assert data["saved"] == 1
    assert len(data["job_ids"]) == 1

    chats = await client.get("/api/v1/whatsapp-monitor/chats")
    updated = next(c for c in chats.json() if c["id"] == chat_id)
    assert updated["last_checked_at"] is not None


@pytest.mark.asyncio
async def test_scan_chat_requires_existing_chat(client: AsyncClient):
    response = await client.post("/api/v1/whatsapp-monitor/chats/999999/scan")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_scan_chat_surfaces_specific_error_reason(client: AsyncClient, monkeypatch):
    create = await client.post(
        "/api/v1/whatsapp-monitor/chats",
        json={"chat_url": CHAT_URL, "label": CHAT_LABEL, "chat_type": "channel"},
    )
    chat_id = create.json()["id"]

    async def fake_scan_chat(label, url, chat_type=None, **kwargs):
        raise WhatsAppScanError(
            "لازم تربط واتساب الأول (تسجيل دخول بالـ QR) قبل ما نقدر نفحص أي شات."
        )

    monkeypatch.setattr(router_module, "scan_chat", fake_scan_chat)

    response = await client.post(f"/api/v1/whatsapp-monitor/chats/{chat_id}/scan")

    assert response.status_code == 502
    assert "تسجيل دخول" in response.json()["message"]
