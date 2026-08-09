import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.scheduler.jobs import scan_whatsapp_chats
from smarthunt.whatsapp_monitor import chat_scanner
from smarthunt.whatsapp_monitor.models import MonitoredWhatsAppChat

"""Regression test for the scheduled scan_whatsapp_chats job added
2026-08-09 (every 3h sweep of every enabled monitored WhatsApp channel/
group) — mirrors test_scheduler_linkedin_jobs.py's pattern exactly."""


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Job).where(Job.source == "whatsapp_message"))
    await db_session.execute(delete(MonitoredWhatsAppChat))
    await db_session.commit()


@pytest.mark.asyncio
async def test_scan_whatsapp_chats_saves_relevant_messages(monkeypatch, db_session: AsyncSession):
    chat = MonitoredWhatsAppChat(
        chat_url="https://whatsapp.com/channel/scheduler-test",
        label="Scheduler Test Channel",
        chat_type="channel",
        enabled=True,
    )
    db_session.add(chat)
    await db_session.commit()
    await db_session.refresh(chat)

    async def fake_scan_chat(label, url, chat_type="group", limit=50, scroll_rounds=10):
        return [
            {
                "text": (
                    "📌 Job Opportunity | Linux System Administrator\n\n"
                    "🏢 Acme Systems\n\n📍 Riyadh, Saudi Arabia\n\n"
                    "🌟 Requirements:\n🔹 5+ years RHEL/Linux administration experience.\n"
                ),
                "post_url": f"{url}#msg-scheduler-test",
            }
        ]

    monkeypatch.setattr(chat_scanner, "scan_chat", fake_scan_chat)

    await scan_whatsapp_chats()

    result = await db_session.execute(select(Job).where(Job.source == "whatsapp_message"))
    saved = result.scalars().all()
    assert len(saved) == 1
    assert saved[0].post_url == "https://whatsapp.com/channel/scheduler-test#msg-scheduler-test"

    await db_session.refresh(chat)
    assert chat.last_checked_at is not None


@pytest.mark.asyncio
async def test_scan_whatsapp_chats_skips_disabled_chats(monkeypatch, db_session: AsyncSession):
    chat = MonitoredWhatsAppChat(
        chat_url="https://whatsapp.com/channel/disabled-test",
        label="Disabled Test Channel",
        chat_type="channel",
        enabled=False,
    )
    db_session.add(chat)
    await db_session.commit()

    called = False

    async def fake_scan_chat(label, url, chat_type="group", limit=50, scroll_rounds=10):
        nonlocal called
        called = True
        return []

    monkeypatch.setattr(chat_scanner, "scan_chat", fake_scan_chat)

    await scan_whatsapp_chats()

    assert called is False


@pytest.mark.asyncio
async def test_scan_whatsapp_chats_continues_past_a_failing_chat(
    monkeypatch, db_session: AsyncSession
):
    failing = MonitoredWhatsAppChat(
        chat_url="https://whatsapp.com/channel/failing-test",
        label="Failing Test Channel",
        chat_type="channel",
        enabled=True,
    )
    working = MonitoredWhatsAppChat(
        chat_url="https://whatsapp.com/channel/working-test",
        label="Working Test Channel",
        chat_type="channel",
        enabled=True,
    )
    db_session.add_all([failing, working])
    await db_session.commit()

    async def fake_scan_chat(label, url, chat_type="group", limit=50, scroll_rounds=10):
        if "failing" in url:
            raise chat_scanner.WhatsAppScanError("فشل الفحص")
        return [
            {
                "text": (
                    "📌 Job Opportunity | Linux System Administrator\n\n"
                    "🏢 Acme Systems\n\n📍 Riyadh, Saudi Arabia\n\n"
                    "🌟 Requirements:\n🔹 5+ years RHEL/Linux administration experience.\n"
                ),
                "post_url": f"{url}#msg-1",
            }
        ]

    monkeypatch.setattr(chat_scanner, "scan_chat", fake_scan_chat)

    await scan_whatsapp_chats()

    result = await db_session.execute(select(Job).where(Job.source == "whatsapp_message"))
    saved = result.scalars().all()
    assert len(saved) == 1
    assert saved[0].post_url == "https://whatsapp.com/channel/working-test#msg-1"
