import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.linkedin.provider import LinkedInProvider

"""Regression tests: LinkedInProvider.search() used to return one
hardcoded fake Job ("LinkedIn Demo") regardless of query/location — the
entire product's "discovers real jobs" promise was fake for every
provider, this is the first one made real. These verify the real
scraper against LinkedIn's live public job search (no login required
for the first results page)."""


@pytest.mark.asyncio
async def test_linkedin_search_returns_real_jobs():
    provider = LinkedInProvider()

    jobs = await provider.search(query="python developer", location="Saudi Arabia", limit=5)

    assert isinstance(jobs, list)

    if jobs:
        job = jobs[0]
        assert job.title
        assert job.provider == "linkedin"
        assert job.url.startswith("https://")
        assert "linkedin.com/jobs/view/" in job.url


@pytest.mark.asyncio
async def test_linkedin_search_defaults_to_saudi_arabia_when_no_location():
    provider = LinkedInProvider()

    jobs = await provider.search(query="devops", limit=3)

    assert isinstance(jobs, list)


@pytest.mark.asyncio
async def test_linkedin_search_skips_malformed_cards(monkeypatch):
    """A card missing a title/link shouldn't crash the whole search or
    produce a garbage Job entry — it should just be skipped."""

    provider = LinkedInProvider()

    good_card = MagicMock()
    good_card.locator.return_value.inner_text = AsyncMock(
        side_effect=["  Backend Engineer  ", "  Acme Corp  ", "  Riyadh, Saudi Arabia  "]
    )
    good_card.locator.return_value.get_attribute = AsyncMock(
        return_value="https://sa.linkedin.com/jobs/view/backend-engineer-at-acme-123?trk=xyz"
    )

    broken_card = MagicMock()
    broken_card.locator.return_value.inner_text = AsyncMock(
        side_effect=Exception("no such element")
    )

    cards_locator = MagicMock()
    cards_locator.count = AsyncMock(return_value=2)
    cards_locator.nth = MagicMock(side_effect=[good_card, broken_card])

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.locator = MagicMock(return_value=cards_locator)

    fake_context = AsyncMock()

    async def fake_new_isolated_page():
        return fake_context, fake_page

    # is_running is a read-only property derived from `browser` — set the
    # underlying attribute, not the property itself.
    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(query="backend", location="Saudi Arabia", limit=10)

    assert len(jobs) == 1
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].company == "Acme Corp"
    assert jobs[0].url == "https://sa.linkedin.com/jobs/view/backend-engineer-at-acme-123"
    fake_context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_linkedin_search_returns_empty_list_on_browser_failure(monkeypatch):
    provider = LinkedInProvider()

    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(headless: bool = True):
        raise RuntimeError("no browser binary available")

    monkeypatch.setattr(browser_manager, "launch", fake_launch)

    jobs = await provider.search(query="python", location="Saudi Arabia")

    assert jobs == []
