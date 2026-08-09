import asyncio
import os
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from smarthunt.logging.logger import logger

LAUNCH_TIMEOUT_SECONDS = 30

_CHROMIUM_LAUNCH_ARGS = [
    "--no-sandbox",
    "--disable-setuid-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
]

# Named contexts (get_page("linkedin"), etc.) persist their cookies/
# localStorage here so a real login survives a container restart —
# found live 2026-08-03: browser.new_context() with no storage_state is
# purely in-memory, so every docker-compose rebuild/redeploy (routine,
# happens many times a session) silently logged the owner out and forced
# a fresh LinkedIn login next time, which is also what was triggering
# LinkedIn's own repeated-login abuse detection. This makes a named
# context behave like a real saved browser profile: log in once, stay
# logged in indefinitely, exactly like the owner's own Chrome profile
# does for LinkedIn/Facebook.
BROWSER_PROFILES_DIR = Path(os.getenv("BROWSER_PROFILES_DIR", "/tmp/smarthunt/browser-profiles"))


class BrowserManager:

    _instance: Optional["BrowserManager"] = None

    def __new__(cls):

        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False

        return cls._instance

    def __init__(self):

        if self._initialized:
            return

        self._initialized = True

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None

        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}

        # Separate from contexts/pages above: a persistent context owns
        # its own dedicated browser process bound to a real on-disk
        # profile directory (launch_persistent_context), not a context
        # inside the single shared self.browser. See get_persistent_page.
        self.persistent_contexts: Dict[str, BrowserContext] = {}
        self.persistent_pages: Dict[str, Page] = {}

        # Serializes launch() across concurrent callers — found live
        # 2026-08-05 chasing "the hourly LinkedIn feed scan basically
        # never returns anything": when a discovery job and the feed/
        # hashtag scan land in the same APScheduler tick (routine on
        # this host, since every interval job's phase resets on every
        # restart), each one saw self.browser is None and raced its own
        # concurrent chromium.launch() — N simultaneous launches fighting
        # for this 3-core host's CPU reliably pushed every one of them
        # past the 30s timeout together, even though a single launch
        # alone takes ~15s idle. Without the lock, the loser(s) would
        # also leak a started `playwright` driver process each time
        # (launch() only tears down its own local references on
        # timeout, not a launch already in flight elsewhere).
        self._launch_lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self.browser is not None

    async def launch(
        self,
        headless: bool = True,
    ) -> None:

        if self.browser is not None:
            return

        async with self._launch_lock:
            # Re-check inside the lock: a caller that waited for another
            # in-flight launch() to finish should just reuse its result
            # instead of launching a second browser.
            if self.browser is not None:
                return

            await self._do_launch(headless)

    async def _do_launch(self, headless: bool) -> None:
        try:
            self.playwright = await asyncio.wait_for(
                async_playwright().start(),
                timeout=LAUNCH_TIMEOUT_SECONDS,
            )

            self.browser = await asyncio.wait_for(
                self.playwright.chromium.launch(
                    headless=headless,
                    args=_CHROMIUM_LAUNCH_ARGS,
                ),
                timeout=LAUNCH_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            # A hung Playwright driver subprocess (seen after many
            # launch/close cycles across different asyncio event loops —
            # each pytest test gets its own loop, and this manager is a
            # process-wide singleton) must fail fast and clearly instead
            # of hanging the caller (a scheduled discovery/apply run, or
            # the test suite / CI) forever.
            self.playwright = None
            self.browser = None
            raise RuntimeError(
                f"Browser launch timed out after {LAUNCH_TIMEOUT_SECONDS}s"
            ) from None

    def _context_options(self) -> dict:
        return {
            "ignore_https_errors": True,
            "viewport": {
                "width": 1366,
                "height": 768,
            },
            "user_agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
        }

    def _profile_path(self, provider: str) -> Path:
        return BROWSER_PROFILES_DIR / f"{provider}.json"

    async def get_page(
        self,
        provider: str,
    ) -> Page:

        if self.browser is None:
            raise RuntimeError("Browser is not started. Call launch() first.")

        if provider not in self.contexts:

            options = self._context_options()

            profile_path = self._profile_path(provider)
            if profile_path.exists():
                options["storage_state"] = str(profile_path)
                logger.info(f"Restored saved browser session for provider={provider}")

            # Same unbounded-hang risk launch() was already fixed for —
            # found live 2026-08-07 during a real audit run: a test hung
            # 30+ minutes here (not in launch(), which had already
            # succeeded) under the exact host CPU contention this project
            # has repeatedly documented (long-lived root-owned Chromium
            # renderer processes pinning 60-70%+ CPU). new_context() on an
            # overloaded browser process has no built-in timeout of its
            # own, so a caller could hang forever with zero recourse.
            try:
                context = await asyncio.wait_for(
                    self.browser.new_context(**options),
                    timeout=LAUNCH_TIMEOUT_SECONDS,
                )
            except asyncio.TimeoutError:
                raise RuntimeError(
                    f"Browser context creation timed out after {LAUNCH_TIMEOUT_SECONDS}s"
                ) from None

            context.set_default_timeout(10000)

            context.set_default_navigation_timeout(10000)

            self.contexts[provider] = context

        if provider not in self.pages or self.pages[provider].is_closed():

            self.pages[provider] = await self.contexts[provider].new_page()

        return self.pages[provider]

    async def save_state(self, provider: str) -> None:
        """Persists the named context's current cookies/localStorage to
        disk so the next get_page(provider) call — even in a brand new
        container — restores this exact session instead of starting
        logged out. Call this after any action that plausibly changed
        auth state (a successful login is the main one)."""
        context = self.contexts.get(provider)
        if context is None:
            return

        try:
            BROWSER_PROFILES_DIR.mkdir(parents=True, exist_ok=True)
            await context.storage_state(path=str(self._profile_path(provider)))
            logger.info(f"Saved browser session for provider={provider}")
        except Exception:
            logger.exception(f"Failed to save browser session for provider={provider}")

    async def new_isolated_page(self, timeout_ms: int = 20000) -> tuple[BrowserContext, Page]:
        """A dedicated context+page for a single one-off task (e.g. an
        unauthenticated search scrape run concurrently with other
        providers), separate from the named, session-persisting contexts
        get_page() manages — reusing a shared named context across
        concurrent callers would race on the same page's navigation.
        Caller is responsible for closing the returned context."""

        if self.browser is None:
            raise RuntimeError("Browser is not started. Call launch() first.")

        try:
            context = await asyncio.wait_for(
                self.browser.new_context(**self._context_options()),
                timeout=LAUNCH_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Browser context creation timed out after {LAUNCH_TIMEOUT_SECONDS}s"
            ) from None
        context.set_default_timeout(timeout_ms)
        context.set_default_navigation_timeout(timeout_ms)

        page = await context.new_page()

        return context, page

    def has_persistent_page(self, provider: str) -> bool:
        """Non-launching check — used by callers that poll status and
        shouldn't spin up a whole dedicated browser process just from
        being asked "are you logged in?" before the owner has ever
        started that flow."""
        page = self.persistent_pages.get(provider)
        return page is not None and not page.is_closed()

    async def get_persistent_page(self, provider: str) -> Page:
        """A page backed by a full, real on-disk browser profile
        (launch_persistent_context) instead of the shared self.browser +
        storage_state snapshot every other named context (get_page)
        relies on for session persistence — found live 2026-08-08: a
        real WhatsApp Web login was lost on the very next backend
        restart despite a valid storage_state.json snapshot, because
        Playwright's storage_state() only captures cookies/localStorage,
        never IndexedDB — and WhatsApp Web's multi-device linking stores
        its actual session crypto keys in IndexedDB, not cookies. A full
        profile directory (what this uses) persists everything, the same
        way the owner's own desktop Chrome profile would, so no explicit
        save_state() call is needed or meaningful here (unlike get_page's
        contexts) — the browser's own on-disk profile writes as it goes.

        Costs a dedicated Chromium process per persistent provider (a
        launch_persistent_context owns its own browser, it can't share
        self.browser the way a regular new_context() does) — only use
        this for a provider that actually needs it, not as a default."""
        if provider in self.persistent_pages and not self.persistent_pages[provider].is_closed():
            return self.persistent_pages[provider]

        if self.playwright is None:
            try:
                self.playwright = await asyncio.wait_for(
                    async_playwright().start(), timeout=LAUNCH_TIMEOUT_SECONDS
                )
            except asyncio.TimeoutError:
                self.playwright = None
                raise RuntimeError(
                    f"Playwright driver start timed out after {LAUNCH_TIMEOUT_SECONDS}s"
                ) from None

        profile_dir = BROWSER_PROFILES_DIR / f"{provider}-persistent-profile"
        profile_dir.mkdir(parents=True, exist_ok=True)

        try:
            context = await asyncio.wait_for(
                self.playwright.chromium.launch_persistent_context(
                    str(profile_dir),
                    headless=True,
                    args=_CHROMIUM_LAUNCH_ARGS,
                    **self._context_options(),
                ),
                timeout=LAUNCH_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise RuntimeError(
                f"Persistent browser context launch timed out after {LAUNCH_TIMEOUT_SECONDS}s"
            ) from None

        context.set_default_timeout(10000)
        context.set_default_navigation_timeout(10000)

        self.persistent_contexts[provider] = context
        page = context.pages[0] if context.pages else await context.new_page()
        self.persistent_pages[provider] = page

        return page

    async def close(self) -> None:

        # Best-effort safety net: capture whatever session state exists
        # right now for every named (non-isolated) context, so an
        # unplanned shutdown doesn't lose a session that was never
        # explicitly saved via save_state() — e.g. a login that
        # succeeded but the caller didn't reach the save_state() call.
        for provider in list(self.contexts.keys()):
            await self.save_state(provider)

        for page in self.pages.values():

            if not page.is_closed():
                await page.close()

        self.pages.clear()

        for context in self.contexts.values():
            await context.close()

        self.contexts.clear()

        # Persistent contexts (get_persistent_page) write their full
        # profile — cookies, localStorage, IndexedDB — to disk as they
        # go, not just at close(); no save_state()-style step is needed
        # or meaningful for them the way it is for self.contexts above.
        # Still close explicitly rather than abandon, for a clean flush.
        for page in self.persistent_pages.values():
            if not page.is_closed():
                try:
                    await page.close()
                except Exception:
                    logger.exception("Failed to close a persistent browser page")

        self.persistent_pages.clear()

        for context in list(self.persistent_contexts.values()):
            try:
                await context.close()
            except Exception:
                logger.exception("Failed to close a persistent browser context")

        self.persistent_contexts.clear()

        if self.browser is not None:
            await self.browser.close()
            self.browser = None

        if self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None


browser_manager = BrowserManager()
