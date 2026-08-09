import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.whatsapp_monitor import service
from smarthunt.whatsapp_monitor.message_parser import is_job_related_message, parse_job_message
from smarthunt.whatsapp_monitor.models import MonitoredWhatsAppChat

# Real sample messages the owner pasted from the "ELITE IT | وظائف تقنية
# معلومات - السعودية" WhatsApp channel 2026-08-08 — neither is actually
# relevant to this owner's Linux/storage/virtualization skill set
# (job_relevance.is_relevant_job_title excludes Manager titles outright,
# and Content Creator names no relevant technology at all), which is
# exactly the point: the structured 📌/🏢/📍 format must still parse
# correctly even for a message that ultimately gets filtered out.
BUSINESS_DEV_MESSAGE = (
    "Job Opportunity | Business Development Manager (AI & Technology Solutions)\n"
    "\n"
    "🏢 Fulers\n"
    "\n"
    "📍 Riyadh, Saudi Arabia\n"
    "\n"
    "🌟 Requirements:\n"
    "🔹 Saudi National.\n"
    "🔹 Bachelor's degree in Business, Engineering, Information Technology, or a "
    "related field.\n"
)

CONTENT_CREATOR_MESSAGE = (
    "📌 Job Opportunity | Senior Content Creator\n"
    "\n"
    "🏢 Mindspire\n"
    "\n"
    "📍 Riyadh, Saudi Arabia\n"
    "\n"
    "🌟 Requirements:\n"
    "🔹 Proven experience in content creation.\n"
)

RELEVANT_STRUCTURED_MESSAGE = (
    "📌 Job Opportunity | Linux System Administrator\n"
    "\n"
    "🏢 Acme Systems\n"
    "\n"
    "📍 Riyadh, Saudi Arabia\n"
    "\n"
    "🌟 Requirements:\n"
    "🔹 5+ years RHEL/Linux administration experience.\n"
    "📩 Apply: jobs@acme-systems.example\n"
)

UNSTRUCTURED_RELEVANT_MESSAGE = (
    "We're hiring a Linux Administrator in Riyadh, Saudi Arabia. Send your CV to apply now."
)

UNSTRUCTURED_IRRELEVANT_MESSAGE = "Good morning everyone, hope you're all doing well today!"


def test_parse_job_message_extracts_title_company_location():
    parsed = parse_job_message(RELEVANT_STRUCTURED_MESSAGE)

    assert parsed.matched_structured_format is True
    assert parsed.title == "Linux System Administrator"
    assert parsed.company == "Acme Systems"
    assert parsed.location == "Riyadh, Saudi Arabia"


def test_parse_job_message_handles_header_without_pin_emoji():
    parsed = parse_job_message(BUSINESS_DEV_MESSAGE)

    assert parsed.matched_structured_format is True
    assert parsed.title == "Business Development Manager (AI & Technology Solutions)"
    assert parsed.company == "Fulers"
    assert parsed.location == "Riyadh, Saudi Arabia"


def test_parse_job_message_falls_back_for_unstructured_text():
    parsed = parse_job_message(UNSTRUCTURED_RELEVANT_MESSAGE)

    assert parsed.matched_structured_format is False
    assert parsed.company == "WhatsApp Channel"
    assert parsed.title


def test_is_job_related_message_accepts_relevant_structured_post():
    assert is_job_related_message(RELEVANT_STRUCTURED_MESSAGE) is True


def test_is_job_related_message_rejects_manager_title():
    assert is_job_related_message(BUSINESS_DEV_MESSAGE) is False


def test_is_job_related_message_rejects_irrelevant_technology():
    assert is_job_related_message(CONTENT_CREATOR_MESSAGE) is False


def test_is_job_related_message_accepts_unstructured_relevant_text():
    assert is_job_related_message(UNSTRUCTURED_RELEVANT_MESSAGE) is True


def test_is_job_related_message_rejects_unstructured_irrelevant_text():
    assert is_job_related_message(UNSTRUCTURED_IRRELEVANT_MESSAGE) is False


def test_is_job_related_message_rejects_empty_text():
    assert is_job_related_message("") is False


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Job).where(Job.source == "whatsapp_message"))
    await db_session.execute(delete(MonitoredWhatsAppChat))
    await db_session.commit()


RELEVANT_MESSAGE_DICT = {
    "text": RELEVANT_STRUCTURED_MESSAGE,
    "post_url": "https://whatsapp.com/channel/0029VbCO2TBEAKWBrwOfNU3O#msg-1",
}

IRRELEVANT_MESSAGE_DICT = {
    "text": CONTENT_CREATOR_MESSAGE,
    "post_url": "https://whatsapp.com/channel/0029VbCO2TBEAKWBrwOfNU3O#msg-2",
}


@pytest.mark.asyncio
async def test_add_list_and_remove_chat(db_session: AsyncSession):
    chat = await service.add_chat(
        db_session,
        "https://whatsapp.com/channel/0029VbCO2TBEAKWBrwOfNU3O",
        "ELITE IT | وظائف تقنية معلومات - السعودية",
        "channel",
    )
    assert chat.enabled is True

    chats = await service.list_chats(db_session)
    assert any(c.id == chat.id for c in chats)

    removed = await service.remove_chat(db_session, chat.id)
    assert removed is True

    chats_after = await service.list_chats(db_session)
    assert not any(c.id == chat.id for c in chats_after)


@pytest.mark.asyncio
async def test_remove_nonexistent_chat_returns_false(db_session: AsyncSession):
    assert await service.remove_chat(db_session, 999999) is False


@pytest.mark.asyncio
async def test_set_chat_enabled(db_session: AsyncSession):
    chat = await service.add_chat(
        db_session, "https://whatsapp.com/channel/abc", "Some Group", "group"
    )

    updated = await service.set_chat_enabled(db_session, chat.id, False)
    assert updated.enabled is False


@pytest.mark.asyncio
async def test_save_message_as_job_stores_relevant_structured_message(db_session: AsyncSession):
    job = await service.save_message_as_job(db_session, RELEVANT_MESSAGE_DICT)

    assert job is not None
    assert job.source == "whatsapp_message"
    assert job.title == "Linux System Administrator"
    assert job.company == "Acme Systems"
    assert job.location == "Riyadh, Saudi Arabia"
    assert job.post_url == RELEVANT_MESSAGE_DICT["post_url"]


@pytest.mark.asyncio
async def test_save_message_as_job_skips_irrelevant_message(db_session: AsyncSession):
    job = await service.save_message_as_job(db_session, IRRELEVANT_MESSAGE_DICT)
    assert job is None


@pytest.mark.asyncio
async def test_save_message_as_job_deduplicates_by_post_url(db_session: AsyncSession):
    first = await service.save_message_as_job(db_session, RELEVANT_MESSAGE_DICT)
    await db_session.commit()

    second = await service.save_message_as_job(db_session, RELEVANT_MESSAGE_DICT)

    assert first is not None
    assert second is None


@pytest.mark.asyncio
async def test_save_message_as_job_deduplicates_by_content_fingerprint(db_session: AsyncSession):
    first = await service.save_message_as_job(db_session, RELEVANT_MESSAGE_DICT)
    await db_session.commit()

    reposted = {
        "text": RELEVANT_STRUCTURED_MESSAGE,
        "post_url": "https://whatsapp.com/channel/0029VbCO2TBEAKWBrwOfNU3O#msg-different",
    }
    second = await service.save_message_as_job(db_session, reposted)

    assert first is not None
    assert second is None


@pytest.mark.asyncio
async def test_scan_and_save_returns_only_saved_jobs(db_session: AsyncSession):
    saved = await service.scan_and_save(
        db_session, [RELEVANT_MESSAGE_DICT, IRRELEVANT_MESSAGE_DICT]
    )

    assert len(saved) == 1
    assert saved[0].post_url == RELEVANT_MESSAGE_DICT["post_url"]


@pytest.mark.asyncio
async def test_mark_chat_checked_sets_timestamp(db_session: AsyncSession):
    chat = await service.add_chat(
        db_session, "https://whatsapp.com/channel/xyz", "Another Group", "group"
    )
    assert chat.last_checked_at is None

    await service.mark_chat_checked(db_session, chat.id)

    chats = await service.list_chats(db_session)
    updated = next(c for c in chats if c.id == chat.id)
    assert updated.last_checked_at is not None


def test_synthesize_message_post_url_uses_message_key_when_present():
    url = service.synthesize_message_post_url("https://whatsapp.com/channel/abc", "true_123", "x")
    assert url == "https://whatsapp.com/channel/abc#msg-true_123"


def test_synthesize_message_post_url_falls_back_to_content_hash():
    url_a = service.synthesize_message_post_url("https://whatsapp.com/channel/abc", None, "hello")
    url_b = service.synthesize_message_post_url("https://whatsapp.com/channel/abc", None, "hello")
    url_c = service.synthesize_message_post_url("https://whatsapp.com/channel/abc", None, "world")

    assert url_a == url_b
    assert url_a != url_c
