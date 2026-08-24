import hashlib
import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.logging.logger import logger
from smarthunt.whatsapp_monitor.message_parser import is_job_related_message, parse_job_message
from smarthunt.whatsapp_monitor.models import MonitoredWhatsAppChat

# Same rationale as linkedin_monitor/service.py's identical constant: the
# exact same job opening can legitimately be reposted (same recruiter
# reposting, or the same message forwarded into a second monitored chat)
# — content is what identifies "the same job," not which specific message
# it happened to arrive in.
_CONTENT_FINGERPRINT_LENGTH = 300


def _content_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return normalized[:_CONTENT_FINGERPRINT_LENGTH]


async def list_chats(db: AsyncSession) -> list[MonitoredWhatsAppChat]:
    result = await db.execute(
        select(MonitoredWhatsAppChat).order_by(MonitoredWhatsAppChat.created_at.desc())
    )
    return list(result.scalars().all())


async def add_chat(
    db: AsyncSession, chat_url: str, label: str, chat_type: str
) -> MonitoredWhatsAppChat:
    chat = MonitoredWhatsAppChat(chat_url=chat_url, label=label, chat_type=chat_type)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def remove_chat(db: AsyncSession, chat_id: int) -> bool:
    result = await db.execute(
        select(MonitoredWhatsAppChat).where(MonitoredWhatsAppChat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        return False
    await db.delete(chat)
    await db.commit()
    return True


async def set_chat_enabled(
    db: AsyncSession, chat_id: int, enabled: bool
) -> MonitoredWhatsAppChat | None:
    result = await db.execute(
        select(MonitoredWhatsAppChat).where(MonitoredWhatsAppChat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    if chat is None:
        return None
    chat.enabled = enabled
    await db.commit()
    await db.refresh(chat)
    return chat


async def mark_chat_checked(db: AsyncSession, chat_id: int) -> None:
    result = await db.execute(
        select(MonitoredWhatsAppChat).where(MonitoredWhatsAppChat.id == chat_id)
    )
    chat = result.scalar_one_or_none()
    if chat is not None:
        chat.last_checked_at = datetime.now(timezone.utc)
        await db.commit()


def synthesize_message_post_url(chat_url: str, message_key: str | None, text: str) -> str:
    """WhatsApp exposes no real per-message permalink — same situation
    linkedin_monitor's feed scan already solved the same way. Prefers a
    stable per-message identifier scraped from the DOM (WhatsApp Web
    message rows typically carry a `data-id` attribute) when the scanner
    found one; falls back to a hash of (chat_url, text) so a message
    without one still gets a real, unique, deterministic anchor rather
    than colliding with every other message in the same chat."""
    key = message_key or hashlib.sha1(f"{chat_url}:{text}".encode()).hexdigest()
    return f"{chat_url}#msg-{key}"


async def save_message_as_job(db: AsyncSession, message: dict) -> Job | None:
    """Filters a scanned WhatsApp message through the same relevance bar
    as the rest of discovery, and stores it as a Job row
    (source="whatsapp_message", post_url set) if it passes and isn't
    already stored. Returns None for an irrelevant or duplicate message —
    not an error, just nothing to save."""
    text = message["text"]

    if not is_job_related_message(text):
        return None

    existing = await db.execute(select(Job).where(Job.post_url == message["post_url"]))
    if existing.scalar_one_or_none() is not None:
        return None

    # Compared against every job's description regardless of source (not
    # just other whatsapp_message rows) — same rationale as
    # linkedin_monitor/service.py's identical widening: the same opening
    # can independently surface as a WhatsApp message AND a LinkedIn post
    # (or vice versa), which a source-scoped check would never catch.
    fingerprint = _content_fingerprint(text)
    existing_messages = await db.execute(select(Job.description))
    for (existing_description,) in existing_messages:
        if existing_description and _content_fingerprint(existing_description) == fingerprint:
            return None

    parsed = parse_job_message(text)

    # A structured "📌 Job Opportunity | ... / 🏢 ..." message carries a
    # real title/company (unlike the "WhatsApp Channel" placeholder the
    # unstructured fallback uses), which is exactly the same signal
    # discovery-sourced jobs are deduped on — catches the same real
    # opening being both scraped from e.g. Tanqeeb/Workable AND forwarded
    # into a monitored WhatsApp channel, worded differently enough that
    # the content fingerprint above wouldn't match.
    if parsed.matched_structured_format:
        if await JobRepository(db).is_duplicate(parsed.title, parsed.company):
            return None

    job = Job(
        title=parsed.title,
        company=parsed.company,
        location=parsed.location or "Saudi Arabia",
        description=text,
        source="whatsapp_message",
        url=message["post_url"],
        post_url=message["post_url"],
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    logger.info(f"whatsapp_message_saved_as_job job_id={job.id} post_url={message['post_url']}")

    return job


async def scan_and_save(db: AsyncSession, messages: list[dict]) -> list[Job]:
    saved: list[Job] = []
    for message in messages:
        job = await save_message_as_job(db, message)
        if job is not None:
            saved.append(job)
    await db.commit()
    return saved
