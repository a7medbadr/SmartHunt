import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.playwright.manager import BrowserManager, browser_manager
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

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

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

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

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

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

    posts = await post_scanner.scan_profile_posts("https://linkedin.com/in/someone", limit=10)

    assert len(posts) == 1
    assert posts[0]["urn"] == "urn:li:activity:333"


@pytest.mark.asyncio
async def test_scan_profile_posts_raises_linkedin_scan_error_on_navigation_failure(monkeypatch):
    """Changed 2026-08-06 from "degrades to an empty list" to "raises with
    a specific reason" per explicit request: the owner wants to know *why*
    a manual scan failed (connection issue? browser down? session busy?)
    instead of a generic error every time. Scheduled callers in
    scheduler/jobs.py still tolerate this via their own existing
    try/except Exception (unchanged) — only the manual/router path surfaces
    the reason now."""
    fake_page = MagicMock()
    fake_page.goto = AsyncMock(side_effect=Exception("navigation failed"))

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

    with pytest.raises(post_scanner.LinkedInScanError) as exc_info:
        await post_scanner.scan_profile_posts("https://linkedin.com/in/someone")

    assert "navigation failed" in exc_info.value.reason


@pytest.mark.asyncio
async def test_scan_profile_posts_raises_specific_reason_when_browser_launch_fails(monkeypatch):
    """Regression: launch() used to be called outside the try/except, so
    a real launch failure (e.g. the 30s timeout in browser_manager.launch())
    propagated as an unhandled exception -> 500 -> the frontend's generic
    "حصل خطأ أثناء الفحص" error. Now raises a classified, specific reason
    instead (see _classify_scan_error)."""
    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(self, headless: bool = True):
        raise RuntimeError("Browser launch timed out after 30s")

    monkeypatch.setattr(BrowserManager, "launch", fake_launch)

    with pytest.raises(post_scanner.LinkedInScanError) as exc_info:
        await post_scanner.scan_profile_posts("https://linkedin.com/in/someone")

    assert "المتصفح" in exc_info.value.reason


@pytest.mark.asyncio
async def test_scan_home_feed_raises_specific_reason_when_browser_launch_fails(monkeypatch):
    monkeypatch.setattr(browser_manager, "browser", None)

    async def fake_launch(self, headless: bool = True):
        raise RuntimeError("Browser launch timed out after 30s")

    monkeypatch.setattr(BrowserManager, "launch", fake_launch)

    with pytest.raises(post_scanner.LinkedInScanError) as exc_info:
        await post_scanner.scan_home_feed()

    assert "المتصفح" in exc_info.value.reason


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

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

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
async def test_scan_home_feed_clicks_more_toggle_before_reading_text(monkeypatch):
    """Regression test: LinkedIn truncates any post past ~3 lines behind a
    "…more" toggle, so a still-collapsed post's inner_text() only returns
    the preview — real Saudi hiring posts routinely put the location or
    "apply now" a couple of lines in, past that cutoff, so
    is_job_related_post() was checking text the post never got to. Found
    live 2026-08-07 chasing "لقينا 50 بوست، وحفظنا 0 وظيفة" despite the
    owner seeing real relevant posts manually. The toggle must get clicked
    (best-effort) before the post's text is read."""
    post = _make_post_locator(
        "feed-commentary_expand-me",
        "Hiring a Linux Administrator in Riyadh, Saudi Arabia — apply now",
    )

    toggle = MagicMock()
    toggle.count = AsyncMock(return_value=1)
    toggle.click = AsyncMock()
    toggle_locator = MagicMock()
    toggle_locator.first = toggle
    post.locator = MagicMock(return_value=toggle_locator)

    containers = MagicMock()
    containers.count = AsyncMock(return_value=1)
    containers.nth = MagicMock(return_value=post)

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.evaluate = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

    posts = await post_scanner.scan_home_feed(limit=10, scroll_rounds=1)

    toggle.click.assert_awaited()
    assert len(posts) == 1
    assert "Riyadh, Saudi Arabia" in posts[0]["text"]


@pytest.mark.asyncio
async def test_scan_home_feed_skips_duplicate_component_keys(monkeypatch):
    post_1 = _make_post_locator("feed-commentary_aaa", "First mention")
    post_2 = _make_post_locator("feed-commentary_aaa", "Same post, seen again")
    posts_by_index = [post_1, post_2]

    containers = MagicMock()
    containers.count = AsyncMock(return_value=2)
    # A plain list-based side_effect is a one-shot iterator that gets
    # exhausted after 2 total calls across the whole test — extraction
    # now runs multiple times (once before scrolling, once per round, see
    # _scan_feed_style_page), so this needs to keep returning consistent
    # results across repeated calls instead.
    containers.nth = MagicMock(side_effect=lambda i: posts_by_index[i])

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.evaluate = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

    posts = await post_scanner.scan_home_feed(limit=10, scroll_rounds=1)

    assert len(posts) == 1


@pytest.mark.asyncio
async def test_scan_home_feed_captures_posts_before_they_get_virtualized_away(monkeypatch):
    """Regression test for a real live bug found 2026-08-06: LinkedIn's
    feed recycles/removes old post DOM nodes as new ones load further
    down while scrolling. The old implementation scrolled first, then
    extracted once at the very end — so raising scroll_rounds to find
    *more* posts actually found *fewer*, because whatever loaded early
    had already been removed from the DOM by the time extraction ran. A
    post visible only during an early round (simulating it later being
    virtualized away) must still end up in the final result."""
    post_early = _make_post_locator("feed-commentary_early", "Hiring an early post")
    post_late = _make_post_locator("feed-commentary_late", "Hiring a late post")

    containers = MagicMock()
    call_count = 0

    async def fake_count():
        nonlocal call_count
        call_count += 1
        # First extraction (before any scrolling) sees only the early
        # post; by the second extraction (after one scroll round), the
        # early post has been "virtualized away" and only the late one
        # that just loaded in is present — simulating real recycling.
        return 1

    def fake_nth(i):
        return post_early if call_count == 1 else post_late

    containers.count = fake_count
    containers.nth = MagicMock(side_effect=fake_nth)

    fake_page = MagicMock()
    fake_page.goto = AsyncMock()
    fake_page.wait_for_timeout = AsyncMock()
    fake_page.evaluate = AsyncMock()
    fake_page.locator = MagicMock(return_value=containers)

    async def fake_get_page(self, provider):
        return fake_page

    monkeypatch.setattr(browser_manager, "browser", MagicMock())
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

    posts = await post_scanner.scan_home_feed(limit=10, scroll_rounds=1)

    urns = {p["urn"] for p in posts}
    assert urns == {"feed-commentary_early", "feed-commentary_late"}


"""_classify_scan_error / LinkedInScanError regression tests: added
2026-08-06 per explicit request — the owner wants a specific, actionable
reason next to a failed scan instead of always seeing the same generic
"حصل خطأ أثناء الفحص، جرب تاني", regardless of whether the real cause was
a connection problem, the browser not starting, or another scan already
using the shared session."""


def test_classify_scan_error_recognizes_timeout():
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    reason = post_scanner._classify_scan_error(PlaywrightTimeoutError("Timeout 30000ms exceeded"))
    assert "الاتصال" in reason


def test_classify_scan_error_recognizes_connection_failure():
    reason = post_scanner._classify_scan_error(
        Exception("net::ERR_CONNECTION_REFUSED at https://www.linkedin.com/feed/")
    )
    assert "الاتصال" in reason


def test_classify_scan_error_recognizes_browser_launch_failure():
    reason = post_scanner._classify_scan_error(RuntimeError("Browser launch timed out after 30s"))
    assert "المتصفح" in reason


def test_classify_scan_error_recognizes_target_closed():
    reason = post_scanner._classify_scan_error(
        Exception("Target page, context or browser has been closed")
    )
    assert "اتقفل" in reason


def test_classify_scan_error_falls_back_to_raw_message_for_unknown_errors():
    reason = post_scanner._classify_scan_error(ValueError("something totally unexpected"))
    assert "something totally unexpected" in reason


@pytest.mark.asyncio
async def test_scan_home_feed_raises_specific_reason_when_session_lock_busy(monkeypatch):
    """The shared LinkedIn page lock (used by every scan function) can be
    held by a long-running scan already in progress — the bounded wait
    (_LOCK_WAIT_TIMEOUT_SECONDS) used to just give up quietly with an
    empty result; now it raises a specific, actionable reason instead."""
    monkeypatch.setattr(browser_manager, "browser", MagicMock())

    async def fake_get_page(self, provider):
        raise AssertionError("should never reach get_page if the lock is busy")

    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

    async with post_scanner._linkedin_page_lock:
        # Lock is already held — patch the wait timeout down so the test
        # doesn't actually wait the real 20s to observe the busy path.
        monkeypatch.setattr(post_scanner, "_LOCK_WAIT_TIMEOUT_SECONDS", 0.05)

        with pytest.raises(post_scanner.LinkedInScanError) as exc_info:
            await post_scanner.scan_home_feed()

    assert "فحص تاني" in exc_info.value.reason


@pytest.mark.asyncio
async def test_scan_hashtag_posts_does_not_double_wrap_the_reason(monkeypatch):
    """scan_hashtag_posts wraps _scan_feed_style_page in its own
    try/except — confirms a LinkedInScanError raised inside isn't
    re-classified/mangled into a generic fallback message on the way out
    (the `except LinkedInScanError: raise` passthrough)."""

    async def fake_scan_feed_style_page(url, limit, scroll_rounds, cutoff_date=None):
        raise post_scanner.LinkedInScanError("سبب محدد جدًا للاختبار")

    monkeypatch.setattr(post_scanner, "_scan_feed_style_page", fake_scan_feed_style_page)

    with pytest.raises(post_scanner.LinkedInScanError) as exc_info:
        await post_scanner.scan_hashtag_posts("Hiring")

    assert exc_info.value.reason == "سبب محدد جدًا للاختبار"
