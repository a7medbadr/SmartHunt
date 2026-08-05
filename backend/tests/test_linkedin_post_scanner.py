import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.linkedin_monitor import post_scanner


def _make_post_locator(urn, text):
    locator = MagicMock()
    locator.get_attribute = AsyncMock(return_value=urn)
    locator.inner_text = AsyncMock(return_value=text)
    return locator


@pytest.mark.asyncio
async def test_scan_profile_posts_extracts_urn_and_text(monkeypatch):
    post_1 = _make_post_locator("urn:li:activity:111", "Hiring a Linux Administrator")
    post_2 = _make_post_locator("urn:li:activity:222", "Team celebration post")

    containers = MagicMock()
    containers.count = AsyncMock(return_value=2)
    containers.nth = MagicMock(side_effect=[post_1, post_2])

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "get_page", fake_get_page)

    posts = await post_scanner.scan_profile_posts("https://linkedin.com/in/someone", limit=10)

    assert len(posts) == 2
    assert posts[0]["urn"] == "urn:li:activity:111"
    assert posts[0]["text"] == "Hiring a Linux Administrator"
    assert posts[0]["post_url"] == "https://www.linkedin.com/feed/update/urn:li:activity:111/"


@pytest.mark.asyncio
async def test_scan_profile_posts_skips_duplicate_urns(monkeypatch):
    post_1 = _make_post_locator("urn:li:activity:111", "First mention")
    post_2 = _make_post_locator("urn:li:activity:111", "Same post, seen again")

    containers = MagicMock()
    containers.count = AsyncMock(return_value=2)
    containers.nth = MagicMock(side_effect=[post_1, post_2])

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "get_page", fake_get_page)

    posts = await post_scanner.scan_profile_posts("https://linkedin.com/in/someone", limit=10)

    assert len(posts) == 1


@pytest.mark.asyncio
async def test_scan_profile_posts_skips_malformed_containers(monkeypatch):
    broken = MagicMock()
    broken.get_attribute = AsyncMock(side_effect=Exception("no such element"))

    good = _make_post_locator("urn:li:activity:333", "Real post")

    containers = MagicMock()
    containers.count = AsyncMock(return_value=2)
    containers.nth = MagicMock(side_effect=[broken, good])

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "get_page", fake_get_page)

    posts = await post_scanner.scan_profile_posts("https://linkedin.com/in/someone", limit=10)

    assert len(posts) == 1
    assert posts[0]["urn"] == "urn:li:activity:333"


@pytest.mark.asyncio
async def test_scan_profile_posts_returns_empty_on_navigation_failure(monkeypatch):
    fake_page = MagicMock()
    fake_page.goto = AsyncMock(side_effect=Exception("navigation failed"))

    async def fake_get_page(provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "get_page", fake_get_page)

    posts = await post_scanner.scan_profile_posts("https://linkedin.com/in/someone")

    assert posts == []


@pytest.mark.asyncio
async def test_scan_profile_posts_returns_empty_when_browser_launch_fails(monkeypatch):
    """Regression: launch() used to be called outside the try/except, so
    a real launch failure (e.g. the 30s timeout in browser_manager.launch())
    propagated as an unhandled exception -> 500 -> the frontend's generic
    "حصل خطأ أثناء الفحص" error, instead of degrading to an empty scan like
    every other failure mode here."""
    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(headless: bool = True):
        raise RuntimeError("Browser launch timed out after 30s")

    monkeypatch.setattr(browser_manager, "launch", fake_launch)

    posts = await post_scanner.scan_profile_posts("https://linkedin.com/in/someone")

    assert posts == []


@pytest.mark.asyncio
async def test_scan_home_feed_returns_empty_when_browser_launch_fails(monkeypatch):
    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(headless: bool = True):
        raise RuntimeError("Browser launch timed out after 30s")

    monkeypatch.setattr(browser_manager, "launch", fake_launch)

    posts = await post_scanner.scan_home_feed()

    assert posts == []


@pytest.mark.asyncio
async def test_scan_home_feed_scrolls_and_extracts(monkeypatch):
    """Regression test: the home feed's real markup (confirmed live
    2026-08-04) has zero `data-urn` attributes anywhere on the page —
    LinkedIn renders it with obfuscated CSS classes now, unlike profile
    "recent activity" pages, which still use data-urn. scan_home_feed
    must extract via each post's `componentkey="feed-commentary_<uuid>"`
    attribute instead, and its post_url must be a real (if not exactly
    per-post) LinkedIn link, not empty/broken."""
    post = _make_post_locator("feed-commentary_1878cec5-a8a0-44b1-bd95-1c413d0d2a18", "A feed post")

    containers = MagicMock()
    containers.count = AsyncMock(return_value=1)
    containers.nth = MagicMock(return_value=post)

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.evaluate = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "get_page", fake_get_page)

    posts = await post_scanner.scan_home_feed(limit=10, scroll_rounds=2)

    assert len(posts) == 1
    assert posts[0]["urn"] == "feed-commentary_1878cec5-a8a0-44b1-bd95-1c413d0d2a18"
    assert posts[0]["text"] == "A feed post"
    assert posts[0]["post_url"].startswith("https://www.linkedin.com/feed/")
    # 2 scroll rounds + the clipboard-permission grant path — just assert
    # the real scroll call (document.querySelector('main').scrollBy) fired
    # scroll_rounds times, not an exact total evaluate() call count.
    scroll_calls = [
        call for call in fake_page.evaluate.await_args_list if "scrollBy" in call.args[0]
    ]
    assert len(scroll_calls) == 2
    fake_page.locator.assert_called_with(post_scanner.FEED_POST_SELECTOR)


@pytest.mark.asyncio
async def test_scan_home_feed_skips_duplicate_component_keys(monkeypatch):
    post_1 = _make_post_locator("feed-commentary_aaa", "First mention")
    post_2 = _make_post_locator("feed-commentary_aaa", "Same post, seen again")

    containers = MagicMock()
    containers.count = AsyncMock(return_value=2)
    containers.nth = MagicMock(side_effect=[post_1, post_2])

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.evaluate = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(browser_manager, "get_page", fake_get_page)

    posts = await post_scanner.scan_home_feed(limit=10, scroll_rounds=1)

    assert len(posts) == 1
