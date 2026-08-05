from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.linkedin_monitor.models import MonitoredLinkedInAccount
from smarthunt.linkedin_monitor.relevance import is_job_related_post, synthesize_title
from smarthunt.logging.logger import logger


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
