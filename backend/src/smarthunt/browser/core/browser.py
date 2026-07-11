from playwright.async_api import Browser, BrowserContext, Page, async_playwright


class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser: Browser | None = None

    async def start(self):
        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=True,
        )

        return self

    async def new_page(self) -> Page:
        context: BrowserContext = await self.browser.new_context()

        page = await context.new_page()

        return page

    async def stop(self):
        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()
