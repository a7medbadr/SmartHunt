import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.playwright.manager import BrowserManager, browser_manager
from smarthunt.providers.linkedin.provider import POSTED_DATE_SELECTOR, LinkedInProvider

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

    async def fake_new_isolated_page(self):
        return fake_context, fake_page

    # is_running is a read-only property derived from `browser` — set the
    # underlying attribute, not the property itself.
    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(query="backend", location="Saudi Arabia", limit=10)

    assert len(jobs) == 1
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].company == "Acme Corp"
    assert jobs[0].url == "https://sa.linkedin.com/jobs/view/backend-engineer-at-acme-123"
    fake_context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_linkedin_search_extracts_posted_at_from_listdate(monkeypatch):
    """Confirmed live 2026-08-04: LinkedIn's real job-search cards carry
    a `<time class="job-search-card__listdate--new">` element with a real
    ISO `datetime` attribute (e.g. datetime="2026-07-20"), distinct from
    when SmartHunt itself discovers the job — used to populate
    Job.posted_at. LinkedIn renamed this from the older
    `.job-search-card__listdate` at some point; POSTED_DATE_SELECTOR
    matches both."""

    provider = LinkedInProvider()

    def make_locator(text=None, attr=None):
        locator = MagicMock()
        locator.inner_text = AsyncMock(return_value=text)
        locator.get_attribute = AsyncMock(return_value=attr)
        locator.first = locator
        return locator

    good_card = MagicMock()

    def locator_side_effect(selector):
        return {
            ".base-search-card__title": make_locator(text="Backend Engineer"),
            ".base-search-card__subtitle": make_locator(text="Acme Corp"),
            ".job-search-card__location": make_locator(text="Riyadh, Saudi Arabia"),
            "a.base-card__full-link": make_locator(
                attr="https://sa.linkedin.com/jobs/view/backend-engineer-at-acme-123?trk=xyz"
            ),
            POSTED_DATE_SELECTOR: make_locator(attr="2026-07-20"),
        }[selector]

    good_card.locator = MagicMock(side_effect=locator_side_effect)

    cards_locator = MagicMock()
    cards_locator.count = AsyncMock(return_value=1)
    cards_locator.nth = MagicMock(return_value=good_card)

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.locator = MagicMock(return_value=cards_locator)

    fake_context = AsyncMock()

    async def fake_new_isolated_page(self):
        return fake_context, fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(query="backend", location="Saudi Arabia", limit=10)

    assert len(jobs) == 1
    assert jobs[0].posted_at is not None
    assert jobs[0].posted_at.isoformat() == "2026-07-20"


@pytest.mark.asyncio
async def test_linkedin_search_fetches_real_description_from_job_detail_page(monkeypatch):
    """Regression test: the search-results card has no description text
    at all (confirmed live 2026-08-03 inspecting its real markup) — every
    stored job's description/requirements were empty, which is why
    match() always scored 0% regardless of the real resume. search()
    must now visit each job's own detail page (viewable anonymously,
    same as the search page) for the real description."""

    provider = LinkedInProvider()

    def make_locator(text=None, attr=None):
        locator = MagicMock()
        locator.inner_text = AsyncMock(return_value=text)
        locator.get_attribute = AsyncMock(return_value=attr)
        locator.first = locator
        return locator

    good_card = MagicMock()

    def card_locator_side_effect(selector):
        return {
            ".base-search-card__title": make_locator(text="Linux Administrator"),
            ".base-search-card__subtitle": make_locator(text="Acme Corp"),
            ".job-search-card__location": make_locator(text="Riyadh, Saudi Arabia"),
            "a.base-card__full-link": make_locator(
                attr="https://sa.linkedin.com/jobs/view/linux-admin-at-acme-123?trk=xyz"
            ),
            POSTED_DATE_SELECTOR: make_locator(attr="2026-07-20"),
        }[selector]

    good_card.locator = MagicMock(side_effect=card_locator_side_effect)

    cards_locator = MagicMock()
    cards_locator.count = AsyncMock(return_value=1)
    cards_locator.nth = MagicMock(return_value=good_card)

    description_locator = make_locator(
        text="We need an experienced Linux Administrator with RHEL and Ansible skills."
    )
    description_locator.count = AsyncMock(return_value=1)
    description_locator.first = description_locator

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()

    def page_locator_side_effect(selector):
        if selector == ".job-search-card":
            return cards_locator
        # DESCRIPTION_SELECTOR — the job detail page's own description.
        return description_locator

    fake_page.locator = MagicMock(side_effect=page_locator_side_effect)

    fake_context = AsyncMock()

    async def fake_new_isolated_page(self):
        return fake_context, fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(query="linux", location="Saudi Arabia", limit=10)

    assert len(jobs) == 1
    assert jobs[0].description == (
        "We need an experienced Linux Administrator with RHEL and Ansible skills."
    )
    # Navigated to the search results page, then the job's own detail page.
    assert fake_page.goto.await_count == 2
    assert (
        fake_page.goto.await_args_list[1].args[0]
        == "https://sa.linkedin.com/jobs/view/linux-admin-at-acme-123"
    )


@pytest.mark.asyncio
async def test_linkedin_search_returns_empty_list_on_browser_failure(monkeypatch):
    provider = LinkedInProvider()

    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(self, headless: bool = True):
        raise RuntimeError("no browser binary available")

    monkeypatch.setattr(BrowserManager, "launch", fake_launch)

    jobs = await provider.search(query="python", location="Saudi Arabia")

    assert jobs == []
