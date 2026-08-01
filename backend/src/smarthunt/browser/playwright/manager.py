from typing import Dict, Optional

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)


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

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )

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

    async def get_page(
        self,
        provider: str,
    ) -> Page:

        if self.browser is None:
            raise RuntimeError("Browser is not started. Call launch() first.")

        if provider not in self.contexts:

            context = await self.browser.new_context(**self._context_options())

            context.set_default_timeout(10000)

            context.set_default_navigation_timeout(10000)

            self.contexts[provider] = context

        if provider not in self.pages or self.pages[provider].is_closed():

            self.pages[provider] = await self.contexts[provider].new_page()

        return self.pages[provider]

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
