import asyncio
import logging

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.whatsapp_monitor.service import synthesize_message_post_url

logger = logging.getLogger("smarthunt.whatsapp_monitor")

WHATSAPP_WEB_URL = "https://web.whatsapp.com"
WHATSAPP_PROVIDER = "whatsapp"

# First-draft selectors against well-known, structurally-stable WhatsApp
# Web conventions — CANNOT be verified without a live logged-in session
# (no Chrome-extension/browser access at plan time). Treat these as a
# first draft to verify/correct during the first real live scan, exactly
# like LinkedIn's selectors have already moved twice (see CLAUDE.md's
# LinkedIn login/feed-scan notes) — do not assume correct on first try.
#
# QR_CODE_SELECTOR confirmed live 2026-08-08 against a real logged-out
# session: the container carries a stable `data-testid="link-device-qr-
# code"` (preferred — semantic, not styling), the canvas itself inside it
# has `aria-label="Scan this QR code to link a device!"` (fallback). Ready
# only ~1-4s after navigation, not immediately on page load — screenshot
# callers must wait_for it, not grab it right after goto() (see
# whatsapp_monitor/router.py's _screenshot_login_page).
QR_CODE_SELECTOR = "div[data-testid='link-device-qr-code'], canvas[aria-label]"

# Deliberately NOT the same selector _open_chat below uses to type into
# the search box: is_logged_in only needs *a* stable marker that the real
# chat list has loaded, not specifically the search input, and a "What's
# new on WhatsApp Web" modal (confirmed live 2026-08-08, appears right
# after a fresh QR login) sits on top of the search box without removing
# it from the DOM — Playwright's default "visible" wait only checks
# layout visibility, not whether another element visually covers it, so
# in principle the search box alone should still work here too, but
# #pane-side (the side panel holding the whole chat list) is a longer-
# standing, more structural marker in WhatsApp Web's DOM that multiple
# independent automation tools have relied on for years — a safer first
# choice than a single guessed contenteditable selector.
LOGGED_IN_MARKER_SELECTOR = "#pane-side, div[data-testid='chat-list']"
# Confirmed live 2026-08-09 against a real logged-in session: WhatsApp
# Web's sidebar search is now a real `<input role="textbox" aria-
# label="Search or start a new chat">`, not a contenteditable div (the
# first-draft guess above, kept as a fallback in case it reverts) — this
# was the actual root cause of every real scan attempt timing out on
# `search_box.click()` before this fix, not a lock/timing issue.
SEARCH_BOX_SELECTOR = (
    'input[aria-label="Search or start a new chat"], '
    'input[aria-label*="Search" i], '
    'div[contenteditable="true"][data-tab="3"], '
    'div[aria-label="Search input textbox"]'
)

# Confirmed live 2026-08-09 inside a real Channel (see CHANNELS_BUTTON_
# SELECTOR below): channel posts render as `#main [data-id]` — a
# completely different DOM shape from the div.message-in/message-out
# bubbles regular chats/groups use (kept as a fallback for the group
# case, still unverified live). `data-id` is WhatsApp's own real message
# identifier (confirmed real values like "ACCBFBA402F16A8FCE..."), a far
# more stable anchor than any CSS class.
MESSAGE_BUBBLE_SELECTOR = "#main [data-id], div.message-in, div.message-out"
MESSAGE_TEXT_SELECTOR = "span.selectable-text"
MESSAGE_PANE_SELECTOR = 'div[data-testid="conversation-panel-messages"], div#main div.copyable-area'

# WhatsApp Channels (broadcast-only, e.g. the owner's job-posting
# channels) are a completely separate surface from regular chats/groups
# — confirmed live 2026-08-09: the normal sidebar search (SEARCH_BOX_
# SELECTOR below) finds zero results for a followed channel no matter
# how it's typed, because channels aren't indexed in the regular chat
# list/search at all. They live behind their own dedicated rail button.
CHANNELS_BUTTON_SELECTOR = "button[aria-label='Channels']"


class WhatsAppScanError(Exception):
    """Mirrors linkedin_monitor/post_scanner.py's LinkedInScanError
    exactly: carries a specific, human-readable (Arabic) reason instead
    of a generic failure, so the manual/UI-facing router can surface it
    directly rather than a one-size-fits-all "حصل خطأ، جرب تاني"."""

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _classify_scan_error(exc: Exception) -> str:
    message = str(exc).lower()

    if isinstance(exc, PlaywrightTimeoutError) or "timeout" in message:
        return "مشكلة في الاتصال مع واتساب ويب — الصفحة أخدت وقت طويل من غير رد."

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
        return "حصلت مشكلة في الاتصال ما بين المشروع وواتساب ويب — تأكد إن السيرفر متصل بالإنترنت."

    if "browser launch timed out" in message or "browser is not started" in message:
        return "المتصفح مش قادر يشتغل دلوقتي — جرب تاني بعد شوية."

    if "target closed" in message or "target page, context or browser has been closed" in message:
        return "المتصفح اتقفل فجأة أثناء الفحص (غالبًا بسبب إعادة تشغيل أو تنظيف دوري) — جرب تاني."

    return f"حصل خطأ غير متوقع أثناء الفحص: {exc}"


# Serializes all scans (and the QR-login flow) on the single shared
# get_page("whatsapp") page — same rationale as linkedin_monitor's
# _linkedin_page_lock: two scans landing concurrently would navigate the
# same Page object out from under each other.
_whatsapp_page_lock = asyncio.Lock()
_LOCK_WAIT_TIMEOUT_SECONDS = 20


async def _try_acquire_whatsapp_lock() -> bool:
    try:
        await asyncio.wait_for(_whatsapp_page_lock.acquire(), timeout=_LOCK_WAIT_TIMEOUT_SECONDS)
        return True
    except asyncio.TimeoutError:
        return False


async def is_logged_in(page) -> bool:
    """The chat list side pane only renders once WhatsApp Web has loaded
    a real, logged-in session — its absence (QR code still showing, or
    still loading) means not logged in yet. Used both by scan_chat (to
    fail fast with a clear reason) and by the router's login/status poll.

    15s, not a shorter guess: confirmed live 2026-08-08 that a persistent-
    profile page (get_persistent_page) restoring a real prior login after
    a cold container restart can sit on WhatsApp Web's own generic
    "WhatsApp" loading splash for 10-15s before the real chat list
    renders — a real, valid session, just slower to reach steady state
    than a fresh empty context. A shorter timeout here would report
    "not logged in" during that window even though the session is fine."""
    try:
        await page.wait_for_selector(LOGGED_IN_MARKER_SELECTOR, timeout=15000)
        return True
    except Exception:
        return False


async def dismiss_login_overlays(page) -> None:
    """WhatsApp Web showed a one-time "What's new on WhatsApp Web" dialog
    sitting on top of the real chat list right after a fresh QR login —
    confirmed live 2026-08-08. It doesn't block is_logged_in (a
    structural marker outside the dialog), but would block _open_chat's
    search-box click/type below. Best-effort and never raises — most
    scans will find nothing here to close."""
    for selector in (
        "[role='dialog'] button:has-text('Continue')",
        "[role='dialog'] [aria-label='Close']",
        "[role='dialog'] [data-icon='x']",
    ):
        try:
            button = page.locator(selector).first
            if await button.count() > 0:
                await button.click(timeout=2000)
                await page.wait_for_timeout(300)
        except Exception:
            continue


async def _open_chat(page, chat_label: str) -> None:
    """For groups (regular two-way chats WhatsApp's normal sidebar search
    actually indexes) — see _open_channel below for the separate Channels
    surface, confirmed live 2026-08-09 to need a completely different
    path (the normal search finds zero results for a followed Channel,
    full stop, regardless of how the query is typed).

    Confirmed live 2026-08-09: neither a plain .fill() nor a global
    page.keyboard.type() after click() reliably triggers WhatsApp Web's
    own search-results re-render, even though both visibly set the
    input's value (confirmed via screenshot: the search box showed the
    full typed text, red-bordered/active, while the list underneath
    stayed on the unfiltered default chat list). press_sequentially()
    (real, locator-scoped per-character key events — auto-focuses first)
    is what real user typing actually looks like to WhatsApp's own
    keyup-driven search listener; a plain value-only "input" event isn't
    enough. Clicks the first result row unconditionally rather than
    requiring an exact `span[title=...]` match, in case WhatsApp's search
    ranking doesn't put an exact name match strictly first."""
    search_box = page.locator(SEARCH_BOX_SELECTOR).first
    await search_box.click(timeout=10000)
    await search_box.press_sequentially(chat_label, delay=40)
    await page.wait_for_timeout(2500)

    results = page.locator("#pane-side [role='row']")
    if await results.count() == 0:
        raise WhatsAppScanError(
            f'معلقيناش جروب اسمه "{chat_label}" في شريط البحث — تأكد إن الاسم مطابق '
            "تمامًا لاسم الجروب في واتساب."
        )

    await results.first.click(timeout=10000)
    await page.wait_for_timeout(1000)
    await page.keyboard.press("Escape")


async def _open_channel(page, chat_label: str) -> None:
    """WhatsApp Channels live behind their own dedicated rail button
    (CHANNELS_BUTTON_SELECTOR), not the regular chat search — confirmed
    live 2026-08-09 against the owner's real "ELITE IT" channel. Once
    there, a followed channel's row DOES carry an exact `span[title=...]`
    match to its real display name (unlike the group/chat search path
    above, this one is reliable — confirmed with the label's exact
    trailing flag emoji intact)."""
    await page.locator(CHANNELS_BUTTON_SELECTOR).first.click(timeout=10000)

    row = page.locator(f"span[title='{chat_label}']").first
    try:
        await row.wait_for(state="visible", timeout=10000)
    except Exception:
        raise WhatsAppScanError(
            f'معلقيناش قناة اسمها "{chat_label}" في تابة Channels — تأكد إنك متابعها '
            "فعلاً وإن الاسم مطابق تمامًا لاسم القناة في واتساب."
        )

    await row.click(timeout=10000)
    await page.wait_for_timeout(1000)


async def _extract_messages(page, limit: int) -> list[dict]:
    messages: list[dict] = []
    bubbles = page.locator(MESSAGE_BUBBLE_SELECTOR)
    count = min(await bubbles.count(), limit)

    for i in range(count):
        bubble = bubbles.nth(i)
        try:
            text_parts = await bubble.locator(MESSAGE_TEXT_SELECTOR).all_inner_texts()
            text = "\n".join(part.strip() for part in text_parts if part.strip())
            if not text:
                continue
            message_key = await bubble.get_attribute("data-id")
            messages.append({"message_key": message_key, "text": text})
        except Exception:
            # A single malformed message shouldn't fail the whole scan.
            continue

    return messages


async def scan_chat(
    chat_label: str,
    chat_url: str,
    chat_type: str = "group",
    limit: int = 50,
    scroll_rounds: int = 10,
) -> list[dict]:
    """Opens `chat_label` (searched by exact display name — see
    MonitoredWhatsAppChat.label's docstring for why URL isn't enough) and
    reads its most recent messages, scrolling upward a bounded number of
    times to load more history. `chat_type` picks the real, confirmed-
    live navigation path: "channel" opens via the dedicated Channels rail
    button (_open_channel — the regular chat search finds zero results
    for a followed channel), anything else (groups) uses the regular
    sidebar search (_open_chat). Returns `{text, post_url}` dicts, same
    shape linkedin_monitor's scanners return, ready for
    service.scan_and_save."""
    if not await _try_acquire_whatsapp_lock():
        logger.warning("whatsapp_chat_scan_lock_busy", extra={"chat_label": chat_label})
        raise WhatsAppScanError("فيه فحص تاني شغال دلوقتي على نفس السيشن — استنى شوية وجرب تاني.")

    try:
        page = await browser_manager.get_persistent_page(WHATSAPP_PROVIDER)

        if "web.whatsapp.com" not in page.url:
            await page.goto(WHATSAPP_WEB_URL, wait_until="domcontentloaded", timeout=30000)

        if not await is_logged_in(page):
            raise WhatsAppScanError(
                "لازم تربط واتساب الأول (تسجيل دخول بالـ QR) قبل ما نقدر نفحص أي شات."
            )

        await dismiss_login_overlays(page)
        if chat_type == "channel":
            await _open_channel(page, chat_label)
        else:
            await _open_chat(page, chat_label)

        seen_keys: set[str] = set()
        raw_messages: list[dict] = []

        def _collect(batch: list[dict]) -> None:
            for item in batch:
                key = item["message_key"] or item["text"]
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                raw_messages.append(item)

        _collect(await _extract_messages(page, limit))

        for _ in range(scroll_rounds):
            if len(raw_messages) >= limit:
                break
            await page.evaluate(
                f"() => document.querySelector('{MESSAGE_PANE_SELECTOR.split(',')[0].strip()}')"
                "?.scrollBy(0, -2000)"
            )
            await page.wait_for_timeout(1000)
            _collect(await _extract_messages(page, limit))

        messages = [
            {
                "text": item["text"],
                "post_url": synthesize_message_post_url(
                    chat_url, item["message_key"], item["text"]
                ),
            }
            for item in raw_messages
        ]
    except WhatsAppScanError:
        raise
    except Exception as exc:
        logger.exception("whatsapp_chat_scan_failed", extra={"chat_label": chat_label})
        raise WhatsAppScanError(_classify_scan_error(exc)) from exc
    finally:
        _whatsapp_page_lock.release()

    logger.info(
        "whatsapp_chat_scan_completed", extra={"chat_label": chat_label, "found": len(messages)}
    )

    return messages
