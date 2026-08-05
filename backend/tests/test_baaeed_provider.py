import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.baaeed.provider import BaaeedProvider

"""Baaeed (baaeed.com, a Hsoub product) is a real remote-jobs board —
unlike Mihnati/Wellfound/Glassdoor (all confirmed Cloudflare/bot-walled,
see CLAUDE.md), a plain headless request gets real content: confirmed
live 2026-08-03 scraping its actual `/remote-jobs` listing page
(`.item__details` cards). Every listing is remote, not tied to a
physical Saudi location — see the provider module's own docstring for
why that's a real scope decision against the Saudi-only discovery
filter, not a bug here."""


@pytest.mark.asyncio
async def test_baaeed_search_returns_real_jobs():
    provider = BaaeedProvider()

    jobs = await provider.search(limit=5)

    assert isinstance(jobs, list)

    if jobs:
        job = jobs[0]
        assert job.title
        assert job.company
        assert job.provider == "baaeed"
        assert job.url.startswith("https://baaeed.com/")
        assert job.location == "Remote"


@pytest.mark.asyncio
async def test_baaeed_search_skips_malformed_cards(monkeypatch):
    provider = BaaeedProvider()

    def make_locator(text=None, attr=None):
        locator = MagicMock()
        locator.inner_text = AsyncMock(return_value=text)
        locator.get_attribute = AsyncMock(return_value=attr)
        locator.first = locator
        return locator

    good_card = MagicMock()

    # card.locator("ul...li").first.locator("a") is a two-level chain —
    # the outer locator's own .locator("a") must resolve to the company
    # text, not the outer locator itself.
    company_link = make_locator(text="Acme Corp")
    meta_items = make_locator()
    meta_items.locator = MagicMock(return_value=company_link)

    def good_locator_side_effect(selector):
        return {
            "h3.card-title a": make_locator(
                text="Linux Administrator",
                attr="https://baaeed.com/remote-jobs/linux-admin-at-acme",
            ),
            "ul.baaeed-list__meta-items li": meta_items,
        }[selector]

    good_card.locator = MagicMock(side_effect=good_locator_side_effect)

    broken_card = MagicMock()
    broken_card.locator = MagicMock(side_effect=Exception("no such element"))

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

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(limit=10)

    assert len(jobs) == 1
    assert jobs[0].title == "Linux Administrator"
    assert jobs[0].company == "Acme Corp"
    assert jobs[0].url == "https://baaeed.com/remote-jobs/linux-admin-at-acme"
    fake_context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_baaeed_search_returns_empty_list_on_browser_failure(monkeypatch):
    provider = BaaeedProvider()

    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(headless: bool = True):
        raise RuntimeError("no browser binary available")

    monkeypatch.setattr(browser_manager, "launch", fake_launch)

    jobs = await provider.search()

    assert jobs == []
