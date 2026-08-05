import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.linkedin_monitor import service
from smarthunt.linkedin_monitor.models import MonitoredLinkedInAccount


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Job).where(Job.source == "linkedin_post"))
    await db_session.execute(delete(MonitoredLinkedInAccount))
    await db_session.commit()


RELEVANT_POST = {
    "urn": "urn:li:activity:1234",
    "text": (
        "We're hiring a Linux Administrator in Riyadh, Saudi Arabia. " "Send your CV to apply now."
    ),
    "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:1234/",
}

IRRELEVANT_POST = {
    "urn": "urn:li:activity:5678",
    "text": "Just celebrated our team's anniversary!",
    "post_url": "https://www.linkedin.com/feed/update/urn:li:activity:5678/",
}


@pytest.mark.asyncio
async def test_add_list_and_remove_account(db_session: AsyncSession):
    account = await service.add_account(db_session, "https://linkedin.com/in/someone", "HR lead")
    assert account.enabled is True

    accounts = await service.list_accounts(db_session)
    assert any(a.id == account.id for a in accounts)

    removed = await service.remove_account(db_session, account.id)
    assert removed is True

    accounts_after = await service.list_accounts(db_session)
    assert not any(a.id == account.id for a in accounts_after)


@pytest.mark.asyncio
async def test_remove_nonexistent_account_returns_false(db_session: AsyncSession):
    assert await service.remove_account(db_session, 999999) is False


@pytest.mark.asyncio
async def test_set_account_enabled(db_session: AsyncSession):
    account = await service.add_account(db_session, "https://linkedin.com/in/someone", None)

    updated = await service.set_account_enabled(db_session, account.id, False)
    assert updated.enabled is False


@pytest.mark.asyncio
async def test_save_post_as_job_stores_relevant_post(db_session: AsyncSession):
    job = await service.save_post_as_job(db_session, RELEVANT_POST)

    assert job is not None
    assert job.source == "linkedin_post"
    assert job.post_url == RELEVANT_POST["post_url"]
    assert job.description == RELEVANT_POST["text"]
    assert job.location == "Saudi Arabia"


@pytest.mark.asyncio
async def test_save_post_as_job_skips_irrelevant_post(db_session: AsyncSession):
    job = await service.save_post_as_job(db_session, IRRELEVANT_POST)
    assert job is None


@pytest.mark.asyncio
async def test_save_post_as_job_deduplicates_by_post_url(db_session: AsyncSession):
    first = await service.save_post_as_job(db_session, RELEVANT_POST)
    await db_session.commit()

    second = await service.save_post_as_job(db_session, RELEVANT_POST)

    assert first is not None
    assert second is None


@pytest.mark.asyncio
async def test_scan_and_save_returns_only_saved_jobs(db_session: AsyncSession):
    saved = await service.scan_and_save(db_session, [RELEVANT_POST, IRRELEVANT_POST])

    assert len(saved) == 1
    assert saved[0].post_url == RELEVANT_POST["post_url"]


@pytest.mark.asyncio
async def test_mark_account_checked_sets_timestamp(db_session: AsyncSession):
    account = await service.add_account(db_session, "https://linkedin.com/in/someone", None)
    assert account.last_checked_at is None

    await service.mark_account_checked(db_session, account.id)

    accounts = await service.list_accounts(db_session)
    updated = next(a for a in accounts if a.id == account.id)
    assert updated.last_checked_at is not None
