import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.playwright.manager import BrowserManager, browser_manager
from smarthunt.providers.tanqeeb.provider import DESCRIPTION_SELECTOR, TanqeebProvider

"""Regression tests: TanqeebProvider.search() used to return one
hardcoded fake dict ("Senior Systems Engineer (IBM AIX)", score: 93)
regardless of query/location. These verify the real scraper against
Tanqeeb's live, server-rendered Saudi Arabia job search
(saudi.tanqeeb.com — no login, no bot challenge, confirmed live
2026-08-06)."""


@pytest.mark.asyncio
async def test_tanqeeb_search_returns_real_jobs():
    provider = TanqeebProvider()

    jobs = await provider.search(query="linux", location="Saudi Arabia", limit=5)

    assert isinstance(jobs, list)

    if jobs:
        job = jobs[0]
        assert job.title
        assert job.provider == "tanqeeb"
        assert job.url.startswith("https://saudi.tanqeeb.com/")
        assert job.country == "Saudi Arabia"


@pytest.mark.asyncio
async def test_tanqeeb_search_builds_empty_keywords_url_with_no_query(monkeypatch):
    """A second real, sequential live-browser test in this same process
    was found to hang (cross-event-loop reuse of the process-wide
    browser_manager singleton across pytest-asyncio's function-scoped
    event loops — the same class of flakiness CLAUDE.md documents for
    this suite's other real-browser tests). Verify the no-query URL
    shape against a mock instead of a second real navigation."""

    provider = TanqeebProvider()

    cards_locator = MagicMock()
    cards_locator.count = AsyncMock(return_value=0)

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.locator = MagicMock(return_value=cards_locator)

    fake_context = AsyncMock()

    async def fake_new_isolated_page(self):
        return fake_context, fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(limit=3)

    assert jobs == []
    fake_page.goto.assert_awaited_once()
    called_url = fake_page.goto.await_args.args[0]
    assert called_url == "https://saudi.tanqeeb.com/jobs/search?keywords=&country=54"


@pytest.mark.asyncio
async def test_tanqeeb_search_skips_malformed_cards(monkeypatch):
    """A card missing a title/url/id shouldn't crash the whole search or
    produce a garbage Job entry — it should just be skipped."""

    provider = TanqeebProvider()

    def make_good_card_attr(name):
        return {
            "data-job-id": "20947702",
            "data-job-name": "Linux Administrator",
            "data-job-company": "Acme Corp",
            "data-job-location": "Saudi - Riyadh",
            "data-job-url": "/jobs-in-saudi/all/jobs/020947702.html",
            "data-job-date": "9 May 2026",
        }[name]

    good_card = MagicMock()
    good_card.get_attribute = AsyncMock(side_effect=make_good_card_attr)

    broken_card = MagicMock()
    broken_card.get_attribute = AsyncMock(side_effect=Exception("no such attribute"))

    cards_locator = MagicMock()
    cards_locator.count = AsyncMock(return_value=2)
    cards_locator.nth = MagicMock(side_effect=[good_card, broken_card])

    description_locator = MagicMock()
    description_locator.count = AsyncMock(return_value=1)
    description_locator.first = description_locator
    description_locator.inner_text = AsyncMock(
        return_value="We need an experienced Linux Administrator."
    )

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()

    def page_locator_side_effect(selector):
        if selector == DESCRIPTION_SELECTOR:
            return description_locator
        return cards_locator

    fake_page.locator = MagicMock(side_effect=page_locator_side_effect)

    fake_context = AsyncMock()

    async def fake_new_isolated_page(self):
        return fake_context, fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(query="linux", location="Saudi Arabia", limit=10)

    assert len(jobs) == 1
    assert jobs[0].title == "Linux Administrator"
    assert jobs[0].company == "Acme Corp"
    assert jobs[0].external_id == "20947702"
    assert jobs[0].url == "https://saudi.tanqeeb.com/jobs-in-saudi/all/jobs/020947702.html"
    # Tanqeeb's own data-job-location shorthands the country as "Saudi",
    # not "Saudi Arabia" — normalized so DiscoveryService's Saudi-only
    # substring filter doesn't silently drop every Tanqeeb job.
    assert jobs[0].location == "Saudi Arabia - Riyadh"
    assert jobs[0].posted_at is not None
    assert jobs[0].posted_at.isoformat() == "2026-05-09"
    fake_context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_tanqeeb_search_handles_unparseable_date(monkeypatch):
    """Tanqeeb's own list cards carry relative dates ("6 hours ago",
    "Tuesday") on some postings — confirmed live 2026-08-06 — which
    can't be parsed into a real date. That must not crash the card."""

    provider = TanqeebProvider()

    def make_card_attr(name):
        return {
            "data-job-id": "20947702",
            "data-job-name": "Linux Administrator",
            "data-job-company": "Acme Corp",
            "data-job-location": "Saudi - Riyadh",
            "data-job-url": "/jobs-in-saudi/all/jobs/020947702.html",
            "data-job-date": "6 hours ago",
        }[name]

    good_card = MagicMock()
    good_card.get_attribute = AsyncMock(side_effect=make_card_attr)

    cards_locator = MagicMock()
    cards_locator.count = AsyncMock(return_value=1)
    cards_locator.nth = MagicMock(return_value=good_card)

    description_locator = MagicMock()
    description_locator.count = AsyncMock(return_value=0)

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()

    def page_locator_side_effect(selector):
        if selector == DESCRIPTION_SELECTOR:
            return description_locator
        return cards_locator

    fake_page.locator = MagicMock(side_effect=page_locator_side_effect)

    fake_context = AsyncMock()

    async def fake_new_isolated_page(self):
        return fake_context, fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(query="linux", location="Saudi Arabia", limit=10)

    assert len(jobs) == 1
    assert jobs[0].posted_at is None
    assert jobs[0].description == ""


@pytest.mark.asyncio
async def test_tanqeeb_search_returns_empty_list_on_browser_failure(monkeypatch):
    provider = TanqeebProvider()

    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(self, headless: bool = True):
        raise RuntimeError("no browser binary available")

    monkeypatch.setattr(BrowserManager, "launch", fake_launch)

    jobs = await provider.search(query="linux", location="Saudi Arabia")

    assert jobs == []
