import asyncio
import logging
import re

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.linkedin_monitor.relevance import is_job_related_post

logger = logging.getLogger("smarthunt.linkedin_monitor")


class LinkedInScanError(Exception):
    """Raised by scan_home_feed/scan_hashtag_posts/scan_profile_posts on
    a real failure, carrying a specific, human-readable (Arabic) reason —
    added 2026-08-06 per explicit request: the owner wants to actually
    know *why* a manual scan failed (no connection to LinkedIn? browser
    couldn't start? another scan already running?) instead of always
    seeing the same generic "حصل خطأ أثناء الفحص، جرب تاني" regardless of
    cause. The scheduled callers in scheduler/jobs.py already wrap each
    scan call in their own try/except Exception (defensive redundancy
    from when these functions used to swallow their own errors) — this
    being an Exception subclass means that existing "one hashtag/account
    failing doesn't skip the rest of the batch" resilience is unchanged,
    it's still caught there the same as any other exception. Only the
    router (linkedin_monitor/router.py), which owns the manual/UI-facing
    path, catches this specifically to surface `.reason` back to the
    frontend as the HTTPException detail."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _classify_scan_error(exc: Exception) -> str:
    """Turns a raw exception from a LinkedIn scan into a specific,
    actionable Arabic reason instead of a generic failure message —
    pattern-matches on exception type/message since Playwright wraps
    real browser/network failures (timeouts, DNS/connection errors) into
    fairly generic Error/TimeoutError types with the real cause only
    identifiable from the message text."""
    message = str(exc).lower()

    if isinstance(exc, PlaywrightTimeoutError) or "timeout" in message:
        return "مشكلة في الاتصال مع لينكدان — الصفحة أخدت وقت طويل من غير رد."

    if any(
        marker in message
        for marker in (
            "net::err",
            "econnrefused",
            "econnreset",
            "enotfound",
            "name_not_resolved",
            "internet_disconnected",
        )
    ):
        return (
            "حصلت مشكلة في الاتصال ما بين المشروع وموقع لينكدان — تأكد إن السيرفر متصل بالإنترنت."
        )

    if "browser launch timed out" in message or "browser is not started" in message:
        return "المتصفح مش قادر يشتغل دلوقتي — جرب تاني بعد شوية."

    if "target closed" in message or "target page, context or browser has been closed" in message:
        return "المتصفح اتقفل فجأة أثناء الفحص (غالبًا بسبب إعادة تشغيل أو تنظيف دوري) — جرب تاني."

    return f"حصل خطأ غير متوقع أثناء الفحص: {exc}"


# scan_profile_posts / scan_home_feed / scan_hashtag_posts all navigate the
# same shared, session-persisting get_page("linkedin") — fine one at a
# time (the normal case), but if two of these ever land in the same
# scheduler tick they'd both goto()/scroll/extract on the *same* Page
# object concurrently and corrupt each other's results. Serializes access
# rather than giving each caller its own page, since the whole point of
# the shared named context is to reuse one real, already-logged-in
# session instead of opening a second one.
_linkedin_page_lock = asyncio.Lock()

# scan_hashtags_daily holds this lock for its *entire* ~30+ minute sweep
# across all hashtags (one hashtag at a time, but never releasing between
# them) — found live 2026-08-06 chasing "manual 'scan my home page'
# button always says حصل خطأ أثناء الفحص، جرب تاني": a manual scan
# landing while that daily sweep (or the account sweep) is running used
# to just wait on `async with _linkedin_page_lock` with no bound at all,
# silently queueing for up to ~30 minutes — the frontend's 240s timeout
# fires long before that, showing a generic error even though the
# backend request wasn't actually broken, just stuck in a very long
# queue. A bounded wait here means a manual scan gives up on a busy
# session quickly (scanned=0) instead of hanging until the client times
# out; the scheduled callers already tolerate an empty result the same
# way they tolerate any other transient scan failure.
_LOCK_WAIT_TIMEOUT_SECONDS = 20


async def _try_acquire_linkedin_lock() -> bool:
    try:
        await asyncio.wait_for(_linkedin_page_lock.acquire(), timeout=_LOCK_WAIT_TIMEOUT_SECONDS)
        return True
    except asyncio.TimeoutError:
        return False


# Profile "recent activity" cards' inner_text() includes LinkedIn's own
# surrounding chrome ahead of the real post body — found live 2026-08-05
# chasing saved jobs titled literally "Feed post number 1"/"...number 3"
# (an accessibility landmark heading LinkedIn puts before each card, not
# actual post content) instead of anything like the real
# "🚨 HIRING – FULL STACK DEVELOPER 🚨" that was several lines further in.
# The container is the broadest reliable `data-urn` match; rather than
# chase a narrower selector for just the post body (fragile — this exact
# markup has already reshuffled twice this project, see the module notes
# above), strip known boilerplate LINE patterns instead: the "Feed post
# number N" heading, the author's name/headline (which the raw text
# repeats twice back to back — once from an image alt/aria-label, once
# from the visible text), and the "Xh • Visible to anyone..." timestamp
# line.
_BOILERPLATE_LINE_PATTERNS = [
    re.compile(r"^Feed post number \d+$"),
    re.compile(r"^\s*•\s*Following$"),
    re.compile(r"^Premium\s*•\s*Following$"),
    re.compile(r"^\d+[a-z\s]*•\s*Visible to anyone", re.IGNORECASE),
    # A repost (share) embeds a second whole post card recursively —
    # found live 2026-08-05 on real saved jobs: connection-degree badges
    # ("• 1st", "Premium • 1st", "Verified • 2nd"), bare compact
    # timestamps with no trailing "Visible to anyone" ("1d •", "2h •"),
    # LinkedIn's own hashtag-icon alt text (the literal word "hashtag"
    # preceding each real "#tag"), and a lone "Follow" button label.
    re.compile(r"^•\s*(1st|2nd|3rd)$"),
    re.compile(r"^(Premium|Verified)\s*•\s*(1st|2nd|3rd|Following)$"),
    re.compile(r"^\d+[a-z]*\s*•$", re.IGNORECASE),
    re.compile(r"^hashtag$"),
    re.compile(r"^Follow$"),
]


def _clean_post_text(raw_text: str) -> str:
    lines = raw_text.splitlines()
    cleaned: list[str] = []
    previous_line = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            previous_line = stripped
            continue
        if any(pattern.match(stripped) for pattern in _BOILERPLATE_LINE_PATTERNS):
            continue
        # Author name/headline lines appear twice back-to-back — drop the
        # immediate repeat, not just any later duplicate (a post's real
        # body legitimately repeating a phrase should survive).
        if stripped == previous_line:
            continue
        cleaned.append(stripped)
        previous_line = stripped

    return "\n".join(cleaned).strip()


# Confirmed live 2026-08-04: profile "recent activity" pages (used by
# scan_profile_posts) still carry `[data-urn*='urn:li:activity']` on each
# post container, giving a real, stable per-post permalink — built from
# LinkedIn's known, stable `data-urn` convention.
POST_CONTAINER_SELECTOR = "[data-urn*='urn:li:activity']"

# The home feed (scan_home_feed) is different — found live 2026-08-04 while
# debugging "حصل خطأ أثناء الفحص" reports: the feed's own real HTML has
# ZERO `data-urn` attributes anywhere on the page (LinkedIn now renders it
# with fully obfuscated, hash-like CSS classes, e.g. `_713ca099`), so the
# old shared selector silently found 0 posts every time — the endpoint
# never raised (caught by the try/except below), it just always returned
# scanned=0/saved=0, which the frontend and the owner both read as "did
# this even find anything?" A real per-post marker does still survive
# there: each post's text sits in a `<p componentkey="feed-commentary_
# <uuid>">` — `componentkey` looks to be a stable, semantic attribute
# LinkedIn's own frontend framework uses for its own bookkeeping (unlike
# the CSS classes), not styling, so less likely to get renamed/obfuscated
# on the next redesign than a class name would. There is no real per-post
# permalink left in the feed's DOM anymore (no data-urn, no `feed/update`
# href) — post_url is a synthetic-but-real, unique feed link instead.
FEED_POST_SELECTOR = 'p[componentkey^="feed-commentary_"]'


async def _expand_and_read_text(container) -> str:
    """LinkedIn truncates any post past ~3 lines behind a "…more" toggle —
    inner_text() on a still-collapsed post only returns that truncated
    preview. Found live 2026-08-07 chasing "لقينا 50 بوست، وحفظنا 0 وظيفة"
    reports despite the owner seeing real, relevant Saudi job posts
    manually in the same feed: is_job_related_post() requires a hiring
    signal AND a Saudi location AND a relevant tech title all inside the
    scanned text — real job posts routinely put the location or the
    "apply now"/city name a couple of lines in, past where LinkedIn cuts
    the preview off, so the strict text-match filter was checking against
    text the post never even got to. Best-effort: most posts have no
    toggle at all (nothing to click, inner_text() already has everything),
    so any failure here just falls back to the unexpanded text rather
    than failing the post."""
    try:
        toggle = container.locator(
            'button:has-text("…more"), button:has-text("more"), '
            'span[role="button"]:has-text("…more"), span[role="button"]:has-text("more")'
        ).first
        if await toggle.count() > 0:
            await toggle.click(timeout=3000, force=True)
    except Exception:
        pass

    return (await container.inner_text()).strip()


async def _extract_posts_from_page(page, limit: int) -> list[dict]:
    """Profile "recent activity" pages — real data-urn-based permalinks."""
    posts: list[dict] = []

    containers = page.locator(POST_CONTAINER_SELECTOR)
    count = min(await containers.count(), limit)

    seen_urns: set[str] = set()

    for i in range(count):
        container = containers.nth(i)

        try:
            urn = await container.get_attribute("data-urn")
            if not urn or urn in seen_urns:
                continue
            seen_urns.add(urn)

            text = _clean_post_text(await _expand_and_read_text(container))
            if not text:
                continue

            post_url = f"https://www.linkedin.com/feed/update/{urn}/"

            posts.append({"urn": urn, "text": text, "post_url": post_url})
        except Exception:
            # A single malformed post shouldn't fail the whole scan.
            continue

    return posts


async def _resolve_real_feed_post_url(page, post_container, fallback_url: str) -> str:
    """The feed's own markup has no real per-post permalink (see module
    docstring), but LinkedIn's per-post "..." control menu has a genuine
    "Copy link to post" action that puts the real permalink on the
    clipboard — found live 2026-08-04 while chasing a report that
    clicking through to a feed-sourced job's "original post" link just
    landed back on the home feed instead of the actual post. Only called
    for posts that already passed is_job_related_post (see caller) —
    clicking through this UI costs a couple of real seconds per post, not
    worth paying for the ~45 irrelevant posts in a typical 50-post scan."""
    try:
        menu_button = post_container.locator(
            'button[aria-label^="Open control menu for post"]'
        ).first
        await menu_button.scroll_into_view_if_needed(timeout=8000)
        # A hovering/animating feed reflows constantly, which Playwright's
        # default actionability check (waiting for the element to be
        # perfectly "stable") can fight forever against — force=True
        # skips that check and just clicks at the element's current
        # coordinates, which is fine here since we already confirmed the
        # element exists and scrolled it into view.
        await menu_button.click(timeout=8000, force=True)
        await page.wait_for_timeout(400)

        copy_link_item = page.locator('[role="menuitem"]:has-text("Copy link to post")').first
        await copy_link_item.click(timeout=8000, force=True)

        real_url = await page.evaluate("() => navigator.clipboard.readText()")
        if real_url and real_url.startswith("https://www.linkedin.com/"):
            return real_url.split("?")[0]
    except Exception:
        logger.exception("linkedin_feed_post_url_resolve_failed")
    finally:
        # A left-open dropdown from this post's menu can overlap and
        # block the click on the NEXT post's own menu button — found
        # live 2026-08-04 (2 of 3 posts resolved correctly, the 3rd
        # timed out on its click for exactly this reason). Escape is a
        # no-op if nothing is open, so this is safe to always run.
        try:
            await page.keyboard.press("Escape")
        except Exception:
            pass

    return fallback_url


async def _extract_new_feed_posts(page, seen_keys: set[str], limit: int) -> list[dict]:
    """Extracts whatever FEED_POST_SELECTOR-matching posts are *currently*
    in the DOM that aren't already in `seen_keys` (mutated in place as new
    ones are found) — pulled out of the old single-shot
    _extract_feed_posts_from_page 2026-08-06 so the caller can call this
    repeatedly *during* scrolling instead of once at the very end (see
    _scan_feed_style_page's docstring for why that matters: LinkedIn's
    feed virtualizes/recycles old post DOM nodes as new ones load in, so
    a single end-of-scroll extraction only ever sees whatever's rendered
    near the current scroll position, not everything that was ever
    loaded). No real per-post permalink survives in the obfuscated
    markup by default, so post_url starts as a synthetic-but-real, unique
    link built from the post's own stable `componentkey`; for any post
    that actually looks job-relevant, _resolve_real_feed_post_url
    upgrades that to the real permalink via the post's own "Copy link to
    post" menu action so clicking through from a saved job actually lands
    on that specific post, not just the feed."""
    posts: list[dict] = []

    containers = page.locator(FEED_POST_SELECTOR)
    count = await containers.count()

    for i in range(count):
        if len(seen_keys) >= limit:
            break

        container = containers.nth(i)

        try:
            component_key = await container.get_attribute("componentkey")
            if not component_key or component_key in seen_keys:
                continue
            seen_keys.add(component_key)

            text = await _expand_and_read_text(container)
            if not text:
                continue

            post_url = f"https://www.linkedin.com/feed/#{component_key}"

            if is_job_related_post(text):
                # The post's own container isn't `container` itself (that's
                # just the <p> holding the text) — the control menu button
                # sits a few levels up, in the shared post card.
                post_card = container.locator(
                    "xpath=ancestor::*[.//button[starts-with(@aria-label,"
                    " 'Open control menu for post')]][1]"
                )
                post_url = await _resolve_real_feed_post_url(page, post_card, post_url)

            posts.append({"urn": component_key, "text": text, "post_url": post_url})
        except Exception:
            continue

    return posts


async def scan_profile_posts(profile_url: str, limit: int = 50) -> list[dict]:
    """Scans a specific LinkedIn profile's "recent activity" page for
    their own posts and reposts. Uses the persistent, authenticated
    "linkedin" browser context (same one login()/apply() use) since
    viewing another member's activity requires being logged in."""
    activity_url = profile_url.rstrip("/") + "/recent-activity/all/"

    if not browser_manager.is_running:
        try:
            await browser_manager.launch()
        except Exception as exc:
            logger.exception("linkedin_profile_scan_failed", extra={"profile_url": profile_url})
            raise LinkedInScanError(_classify_scan_error(exc)) from exc

    if not await _try_acquire_linkedin_lock():
        logger.warning("linkedin_profile_scan_lock_busy", extra={"profile_url": profile_url})
        raise LinkedInScanError("فيه فحص تاني شغال دلوقتي على نفس السيشن — استنى شوية وجرب تاني.")

    try:
        page = await browser_manager.get_page("linkedin")

        await page.goto(activity_url, wait_until="domcontentloaded", timeout=30000)
        # Found live 2026-08-04: a blind 3s sleep was flaky — the exact
        # same profile/selector reliably found posts in an isolated
        # manual check, but returned 0 through this endpoint right after
        # a heavy scan_home_feed() call (10 scroll rounds) on the same
        # shared "linkedin" page/context, i.e. genuine page-load timing
        # variance under load, not a wrong selector. Wait for the actual
        # post markup to appear (bounded, so a genuinely-empty activity
        # page still resolves quickly) instead of guessing a fixed delay.
        try:
            await page.wait_for_selector(POST_CONTAINER_SELECTOR, timeout=15000)
        except Exception:
            pass

        posts = await _extract_posts_from_page(page, limit)
    except Exception as exc:
        logger.exception("linkedin_profile_scan_failed", extra={"profile_url": profile_url})
        raise LinkedInScanError(_classify_scan_error(exc)) from exc
    finally:
        _linkedin_page_lock.release()

    logger.info(
        "linkedin_profile_scan_completed",
        extra={"profile_url": profile_url, "found": len(posts)},
    )

    return posts


async def _scan_feed_style_page(url: str, limit: int, scroll_rounds: int) -> list[dict]:
    """Shared navigate/scroll/extract flow for any page that renders the
    same obfuscated feed-post markup (`FEED_POST_SELECTOR`) — the home
    feed itself, and LinkedIn's hashtag pages, which found live
    2026-08-04 actually redirect to `/search/results/all?keywords=%23...`
    rather than staying on `/feed/hashtag/...`, but render posts with the
    exact same component, so the exact same extraction/relevance/real-
    link-resolution logic applies unchanged."""
    if not browser_manager.is_running:
        try:
            await browser_manager.launch()
        except Exception as exc:
            raise LinkedInScanError(_classify_scan_error(exc)) from exc

    if not await _try_acquire_linkedin_lock():
        logger.warning("linkedin_feed_style_scan_lock_busy", extra={"url": url})
        raise LinkedInScanError("فيه فحص تاني شغال دلوقتي على نفس السيشن — استنى شوية وجرب تاني.")

    try:
        page = await browser_manager.get_page("linkedin")

        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        try:
            await page.wait_for_selector(FEED_POST_SELECTOR, timeout=15000)
        except Exception:
            pass

        try:
            await page.context.grant_permissions(["clipboard-read", "clipboard-write"])
        except Exception:
            logger.exception("linkedin_feed_clipboard_permission_failed")

        # page.mouse.wheel() fires at the mouse's current position, which
        # defaults to (0, 0) with no prior mouse.move() — found live
        # 2026-08-05 chasing a report that the hourly feed scan basically
        # never returned new jobs despite running every hour for real: a
        # direct check showed window.scrollY staying at 0 through 10 full
        # wheel rounds, i.e. the "scroll" was a complete no-op the whole
        # time. LinkedIn's feed/search-results pages scroll an inner <main>
        # container, not the window/body (both exactly viewport-height with
        # no overflow) — scrolling that element directly is what actually
        # loads more posts (verified live: post count grew from 2 to 25 over
        # 10 rounds on the home feed, and from 9 to 14 on a hashtag search).
        #
        # Extracts *during* the scroll loop now, not once at the very end
        # — found live 2026-08-06 raising scroll_rounds 10->40 to reach
        # the owner's ~50-post target: a real scan took the expected
        # ~2.5 minutes but found *fewer* posts (10) than the old 10-round/
        # extract-once-at-the-end version found (15). LinkedIn's feed
        # virtualizes/recycles old post DOM nodes as new ones load further
        # down — by the time a single extraction pass ran after all 40
        # rounds, most of what loaded earlier had already been removed
        # from the DOM, so more scrolling was actively making the single
        # end-of-scroll snapshot *worse*, not better. Extracting after
        # every round instead means each newly-loaded batch gets captured
        # before it can be recycled away; seen_keys carries over across
        # rounds so nothing gets double-counted. Also stops scrolling
        # early once `limit` unique posts have been found, instead of
        # always burning the full scroll_rounds budget regardless.
        seen_keys: set[str] = set()
        posts = await _extract_new_feed_posts(page, seen_keys, limit)

        for _ in range(scroll_rounds):
            if len(seen_keys) >= limit:
                break
            await page.evaluate("() => document.querySelector('main')?.scrollBy(0, 2000)")
            await page.wait_for_timeout(2500)
            posts.extend(await _extract_new_feed_posts(page, seen_keys, limit))

        return posts
    except LinkedInScanError:
        raise
    except Exception as exc:
        raise LinkedInScanError(_classify_scan_error(exc)) from exc
    finally:
        _linkedin_page_lock.release()


async def scan_hashtag_posts(hashtag: str, limit: int = 50, scroll_rounds: int = 40) -> list[dict]:
    """Scans the first ~50 posts under a given LinkedIn hashtag (owner-
    supplied, e.g. "Hiring", "SaudiJobs") for job-relevant content — added
    2026-08-05 per explicit request, the hashtag-driven counterpart to
    scan_home_feed/scan_profile_posts. `hashtag` should be given without
    the leading '#'."""
    clean_tag = hashtag.strip().lstrip("#")
    try:
        posts = await _scan_feed_style_page(
            f"https://www.linkedin.com/feed/hashtag/{clean_tag}/", limit, scroll_rounds
        )
        logger.info(
            "linkedin_hashtag_scan_completed", extra={"hashtag": clean_tag, "found": len(posts)}
        )
        return posts
    except LinkedInScanError:
        logger.exception("linkedin_hashtag_scan_failed", extra={"hashtag": clean_tag})
        raise
    except Exception as exc:
        logger.exception("linkedin_hashtag_scan_failed", extra={"hashtag": clean_tag})
        raise LinkedInScanError(_classify_scan_error(exc)) from exc


async def scan_home_feed(limit: int = 50, scroll_rounds: int = 40) -> list[dict]:
    """Scans the owner's own LinkedIn home feed for job-relevant posts
    from anyone (not just monitored accounts) — reposts/shares by
    connections, recruiter posts, etc. Scrolls a bounded number of times
    rather than indefinitely, so a scheduled call has a predictable
    upper bound on how long it runs and how much it interacts with the
    page (see linkedin_monitor/service.py for the hourly pacing this is
    meant to run under). Capped at the first ~50 posts per the owner's
    explicit request, so a scan can't hammer LinkedIn indefinitely."""
    try:
        posts = await _scan_feed_style_page("https://www.linkedin.com/feed/", limit, scroll_rounds)

        logger.info("linkedin_feed_scan_completed", extra={"found": len(posts)})

        return posts

    except LinkedInScanError:
        logger.exception("linkedin_feed_scan_failed")
        raise
    except Exception as exc:
        logger.exception("linkedin_feed_scan_failed")
        raise LinkedInScanError(_classify_scan_error(exc)) from exc
