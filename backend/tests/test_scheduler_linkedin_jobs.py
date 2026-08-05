import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.discovery.service import DiscoveryService
from smarthunt.linkedin_monitor import post_scanner
from smarthunt.linkedin_monitor.models import MonitoredLinkedInAccount
from smarthunt.scheduler.jobs import (
    HASHTAG_LIST,
    daily_morning_discovery,
    scan_all_linkedin_accounts_daily,
    scan_hashtags_daily,
    scan_linkedin_home_feed_hourly,
)

"""Regression tests for the three scheduled jobs added 2026-08-04 (hourly
home-feed scan, once-daily full discovery sweep, once-daily scan of every
monitored LinkedIn account) — added per explicit request that these run
automatically instead of only via the manual buttons."""


@pytest.fixture(autouse=True)
async def cleanup(db_session: AsyncSession):
    yield
    await db_session.execute(delete(Job).where(Job.source == "linkedin_post"))
    await db_session.execute(delete(MonitoredLinkedInAccount))
    await db_session.commit()


@pytest.mark.asyncio
async def test_scan_linkedin_home_feed_hourly_saves_relevant_posts(
    monkeypatch, db_session: AsyncSession
):
    async def fake_scan_home_feed(limit=50, scroll_rounds=10):
        return [
            {
                "urn": "feed-commentary_test-1",
                "text": "Hiring a Linux Administrator in Riyadh, Saudi Arabia.",
                "post_url": "https://www.linkedin.com/feed/#feed-commentary_test-1",
            }
        ]

    monkeypatch.setattr(post_scanner, "scan_home_feed", fake_scan_home_feed)

    await scan_linkedin_home_feed_hourly()

    result = await db_session.execute(select(Job).where(Job.source == "linkedin_post"))
    saved = result.scalars().all()
    assert len(saved) == 1
    assert saved[0].post_url == "https://www.linkedin.com/feed/#feed-commentary_test-1"


@pytest.mark.asyncio
async def test_scan_linkedin_home_feed_hourly_survives_scan_failure(monkeypatch):
    async def fake_scan_home_feed(limit=50, scroll_rounds=10):
        raise RuntimeError("browser unavailable")

    monkeypatch.setattr(post_scanner, "scan_home_feed", fake_scan_home_feed)

    # Must not raise — a scheduled job crashing would just look like a
    # silent no-op to APScheduler, same class of bug as the historical
    # track_scheduler_execution mismatch.
    await scan_linkedin_home_feed_hourly()


@pytest.mark.asyncio
async def test_daily_morning_discovery_runs_every_topic(monkeypatch):
    called_queries = []

    async def fake_discover(self, query, location=None, page=1, limit=25, provider="manual-run"):
        called_queries.append(query)
        return {"providers": 0, "discovered": 0, "inserted": 0, "duplicates": 0}

    monkeypatch.setattr(DiscoveryService, "discover", fake_discover)

    await daily_morning_discovery()

    assert sorted(called_queries) == sorted(
        [
            "Linux Administrator",
            "OpenShift Administrator",
            "VMware Administrator",
            "Storage Administrator",
            "DevOps Engineer",
        ]
    )


@pytest.mark.asyncio
async def test_daily_morning_discovery_continues_past_a_failing_topic(monkeypatch):
    call_count = 0

    async def fake_discover(self, query, location=None, page=1, limit=25, provider="manual-run"):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("provider network error")
        return {"providers": 0, "discovered": 0, "inserted": 0, "duplicates": 0}

    monkeypatch.setattr(DiscoveryService, "discover", fake_discover)

    # Must not raise, and must still attempt the remaining topics.
    await daily_morning_discovery()
    assert call_count == 5


@pytest.mark.asyncio
async def test_scan_all_linkedin_accounts_daily_skips_disabled_accounts(
    monkeypatch, db_session: AsyncSession
):
    enabled = MonitoredLinkedInAccount(
        profile_url="https://linkedin.com/in/enabled-account", enabled=True
    )
    disabled = MonitoredLinkedInAccount(
        profile_url="https://linkedin.com/in/disabled-account", enabled=False
    )
    db_session.add_all([enabled, disabled])
    await db_session.commit()

    scanned_urls = []

    async def fake_scan_profile_posts(profile_url, limit=50):
        scanned_urls.append(profile_url)
        return []

    monkeypatch.setattr(post_scanner, "scan_profile_posts", fake_scan_profile_posts)

    await scan_all_linkedin_accounts_daily()

    assert scanned_urls == ["https://linkedin.com/in/enabled-account"]


@pytest.mark.asyncio
async def test_scan_all_linkedin_accounts_daily_survives_one_account_failing(
    monkeypatch, db_session: AsyncSession
):
    account_a = MonitoredLinkedInAccount(
        profile_url="https://linkedin.com/in/account-a", enabled=True
    )
    account_b = MonitoredLinkedInAccount(
        profile_url="https://linkedin.com/in/account-b", enabled=True
    )
    db_session.add_all([account_a, account_b])
    await db_session.commit()

    scanned_urls = []

    async def fake_scan_profile_posts(profile_url, limit=50):
        scanned_urls.append(profile_url)
        if profile_url == "https://linkedin.com/in/account-a":
            raise RuntimeError("browser unavailable")
        return []

    monkeypatch.setattr(post_scanner, "scan_profile_posts", fake_scan_profile_posts)

    # Must not raise, and both accounts must get scanned even though one
    # fails — list_accounts() orders by created_at desc, so don't assume
    # a specific order here, just that neither got skipped.
    await scan_all_linkedin_accounts_daily()
    assert sorted(scanned_urls) == [
        "https://linkedin.com/in/account-a",
        "https://linkedin.com/in/account-b",
    ]


@pytest.mark.asyncio
async def test_scan_hashtags_daily_scans_every_hashtag(monkeypatch):
    scanned_hashtags = []

    async def fake_scan_hashtag_posts(hashtag, limit=50, scroll_rounds=10):
        scanned_hashtags.append(hashtag)
        return []

    monkeypatch.setattr(post_scanner, "scan_hashtag_posts", fake_scan_hashtag_posts)

    await scan_hashtags_daily()

    assert sorted(scanned_hashtags) == sorted(HASHTAG_LIST)


@pytest.mark.asyncio
async def test_scan_hashtags_daily_continues_past_a_failing_hashtag(monkeypatch):
    call_count = 0

    async def fake_scan_hashtag_posts(hashtag, limit=50, scroll_rounds=10):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("browser unavailable")
        return []

    monkeypatch.setattr(post_scanner, "scan_hashtag_posts", fake_scan_hashtag_posts)

    # Must not raise, and must still attempt every hashtag in the list.
    await scan_hashtags_daily()
    assert call_count == len(HASHTAG_LIST)
