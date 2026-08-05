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

    @property
    def is_running(self) -> bool:
        return self.browser is not None

    async def launch(
        self,
        headless: bool = True,
    ) -> None:

        if self.browser is not None:
            return

        try:
            self.playwright = await asyncio.wait_for(
                async_playwright().start(),
                timeout=LAUNCH_TIMEOUT_SECONDS,
            )

            self.browser = await asyncio.wait_for(
                self.playwright.chromium.launch(
                    headless=headless,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                    ],
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

            context = await self.browser.new_context(**options)

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

        context = await self.browser.new_context(**self._context_options())
        context.set_default_timeout(timeout_ms)
        context.set_default_navigation_timeout(timeout_ms)

        page = await context.new_page()

        return context, page

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

        if self.browser is not None:
            await self.browser.close()
            self.browser = None

        if self.playwright is not None:
            await self.playwright.stop()
            self.playwright = None


browser_manager = BrowserManager()
