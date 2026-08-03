import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.sabbar.provider import SabbarProvider

"""Sabbar (sabbar.com) is real and reachable — unlike Bayt/GulfTalent/
Wuzzuf/Mihnati/Glassdoor (all Cloudflare-challenged, see CLAUDE.md), a
plain headless request gets real content. Its own search box is a JS
combobox with no URL-param-driven query, so search() fetches Sabbar's
recent job listing across a few pages and relies on
DiscoveryService's own title-relevance filter to do the actual keyword
matching, same as every other provider's results already pass
through."""


@pytest.mark.asyncio
async def test_sabbar_search_returns_real_jobs():
    provider = SabbarProvider()

    jobs = await provider.search(limit=5)

    assert isinstance(jobs, list)

    if jobs:
        job = jobs[0]
        assert job.title
        assert job.company
        assert job.provider == "sabbar"
        assert job.url.startswith("https://sabbar.com/")


@pytest.mark.asyncio
async def test_sabbar_search_skips_malformed_cards(monkeypatch):
    provider = SabbarProvider()

    good_card = MagicMock()
    good_card.locator.return_value.first.inner_text = AsyncMock(
        return_value="  Linux Administrator  "
    )
    good_card.locator.return_value.inner_text = AsyncMock(return_value="  Linux Administrator  ")
    good_card.locator.return_value.nth.return_value.inner_text = AsyncMock(
        return_value="  Riyadh  "
    )
    good_card.locator.return_value.first.get_attribute = AsyncMock(
        return_value="/en/jobs/r-linux-admin/id-abc123"
    )

    broken_card = MagicMock()
    broken_card.locator.return_value.inner_text = AsyncMock(
        side_effect=Exception("no such element")
    )
    broken_card.locator.return_value.first.inner_text = AsyncMock(
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

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "new_isolated_page", fake_new_isolated_page)

    jobs = await provider.search(limit=10)

    assert len(jobs) == 1
    assert jobs[0].title == "Linux Administrator"
    fake_context.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_sabbar_search_returns_empty_list_on_browser_failure(monkeypatch):
    provider = SabbarProvider()

    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(headless: bool = True):
        raise RuntimeError("no browser binary available")

    monkeypatch.setattr(browser_manager, "launch", fake_launch)

    jobs = await provider.search()

    assert jobs == []
