import re
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.linkedin_monitor.models import MonitoredHashtag, MonitoredLinkedInAccount
from smarthunt.linkedin_monitor.relevance import is_job_related_post, synthesize_title
from smarthunt.logging.logger import logger

# The same recruiter post text routinely gets published from multiple
# real LinkedIn accounts (an agency posting the same templated opening
# from several recruiters' profiles, or a genuine repost) — found live
# 2026-08-06 via two saved "jobs" with identical text but two different,
# both-genuinely-real post_urls (different activity IDs), so the
# post_url-based dedup below correctly didn't (and shouldn't) catch it.
# Content is what actually identifies "the same job opening" here, not
# the specific post it happened to be copy-pasted into. Normalizes
# whitespace and compares a fixed-length prefix rather than the full
# text — a real duplicate's first few hundred characters (before any
# per-post hashtag-list variation at the tail) are enough to identify it,
# and comparing a bounded prefix keeps this cheap regardless of how long
# a post's full text is.
_CONTENT_FINGERPRINT_LENGTH = 300


def _content_fingerprint(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return normalized[:_CONTENT_FINGERPRINT_LENGTH]


async def list_accounts(db: AsyncSession) -> list[MonitoredLinkedInAccount]:
    result = await db.execute(
        select(MonitoredLinkedInAccount).order_by(MonitoredLinkedInAccount.created_at.desc())
    )
    return list(result.scalars().all())


async def add_account(
    db: AsyncSession, profile_url: str, label: str | None
) -> MonitoredLinkedInAccount:
    account = MonitoredLinkedInAccount(profile_url=profile_url, label=label)
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def remove_account(db: AsyncSession, account_id: int) -> bool:
    result = await db.execute(
        select(MonitoredLinkedInAccount).where(MonitoredLinkedInAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        return False
    await db.delete(account)
    await db.commit()
    return True


async def set_account_enabled(
    db: AsyncSession, account_id: int, enabled: bool
) -> MonitoredLinkedInAccount | None:
    result = await db.execute(
        select(MonitoredLinkedInAccount).where(MonitoredLinkedInAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if account is None:
        return None
    account.enabled = enabled
    await db.commit()
    await db.refresh(account)
    return account


async def list_hashtags(db: AsyncSession) -> list[MonitoredHashtag]:
    result = await db.execute(select(MonitoredHashtag).order_by(MonitoredHashtag.created_at.asc()))
    return list(result.scalars().all())


async def add_hashtag(db: AsyncSession, tag: str) -> MonitoredHashtag:
    clean_tag = tag.strip().lstrip("#")
    hashtag = MonitoredHashtag(tag=clean_tag)
    db.add(hashtag)
    await db.commit()
    await db.refresh(hashtag)
    return hashtag


async def remove_hashtag(db: AsyncSession, hashtag_id: int) -> bool:
    result = await db.execute(select(MonitoredHashtag).where(MonitoredHashtag.id == hashtag_id))
    hashtag = result.scalar_one_or_none()
    if hashtag is None:
        return False
    await db.delete(hashtag)
    await db.commit()
    return True


async def set_hashtag_enabled(
    db: AsyncSession, hashtag_id: int, enabled: bool
) -> MonitoredHashtag | None:
    result = await db.execute(select(MonitoredHashtag).where(MonitoredHashtag.id == hashtag_id))
    hashtag = result.scalar_one_or_none()
    if hashtag is None:
        return None
    hashtag.enabled = enabled
    await db.commit()
    await db.refresh(hashtag)
    return hashtag


async def mark_hashtag_checked(db: AsyncSession, hashtag_id: int) -> None:
    result = await db.execute(select(MonitoredHashtag).where(MonitoredHashtag.id == hashtag_id))
    hashtag = result.scalar_one_or_none()
    if hashtag is not None:
        hashtag.last_checked_at = datetime.now(timezone.utc)
        await db.commit()


async def save_post_as_job(db: AsyncSession, post: dict) -> Job | None:
    """Filters a scanned post through the same relevance bar as the rest
    of discovery, and stores it as a Job row (source="linkedin_post",
    post_url set) if it passes and isn't already stored. Returns None
    for an irrelevant or duplicate post — not an error, just nothing to
    save."""
    text = post["text"]

    if not is_job_related_post(text):
        return None

    existing = await db.execute(select(Job).where(Job.post_url == post["post_url"]))
    if existing.scalar_one_or_none() is not None:
        return None

    fingerprint = _content_fingerprint(text)
    existing_posts = await db.execute(select(Job.description).where(Job.source == "linkedin_post"))
    for (existing_description,) in existing_posts:
        if existing_description and _content_fingerprint(existing_description) == fingerprint:
            return None

    job = Job(
        title=synthesize_title(text),
        company="LinkedIn Post",
        location="Saudi Arabia",
        description=text,
        source="linkedin_post",
        url=post["post_url"],
        post_url=post["post_url"],
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    logger.info(f"linkedin_post_saved_as_job job_id={job.id} post_url={post['post_url']}")

    return job


async def scan_and_save(db: AsyncSession, posts: list[dict]) -> list[Job]:
    saved: list[Job] = []
    for post in posts:
        job = await save_post_as_job(db, post)
        if job is not None:
            saved.append(job)
    await db.commit()
    return saved


async def mark_account_checked(db: AsyncSession, account_id: int) -> None:
    result = await db.execute(
        select(MonitoredLinkedInAccount).where(MonitoredLinkedInAccount.id == account_id)
    )
    account = result.scalar_one_or_none()
    if account is not None:
        account.last_checked_at = datetime.now(timezone.utc)
        await db.commit()
