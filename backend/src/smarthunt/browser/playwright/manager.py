from typing import Dict, Optional

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright


class BrowserManager:
    """
    Singleton responsible for the real Playwright browser lifecycle and a
    per-provider pool of BrowserContext/Page pairs, so each provider (LinkedIn,
    Indeed, ...) gets an isolated browsing context instead of sharing state.
    """

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

    async def launch(self, headless: bool = True) -> None:
        if self.browser is not None:
            return
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)

    async def get_page(self, provider: str) -> Page:
        if self.browser is None:
            raise RuntimeError("Browser is not started. Call launch() first.")

        if provider not in self.contexts:
            self.contexts[provider] = await self.browser.new_context()

        if provider not in self.pages or self.pages[provider].is_closed():
            self.pages[provider] = await self.contexts[provider].new_page()

        return self.pages[provider]

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
