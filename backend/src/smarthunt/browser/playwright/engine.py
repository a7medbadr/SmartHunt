from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.browser.providers.linkedin.login import linkedin_login


class PlaywrightEngine:
    def __init__(self):
        self.manager = browser_manager

    async def start(self) -> dict:
        await self.manager.launch()
        return {"status": "started"}

    async def stop(self) -> dict:
        await self.manager.close()
        return {"status": "stopped"}

    async def login(self, provider: str) -> dict:
        if provider.lower() == "linkedin":
            if not self.manager.is_running:
                await self.manager.launch()
            page = await self.manager.get_page(provider)
            result = await linkedin_login(page)
            return {**result, "provider": provider}

        return {"status": "SUCCESS", "provider": provider}

    async def open_job(self, url: str) -> dict:
        return {"status": "SUCCESS", "job_url": url}

    async def apply(self, job_url: str) -> dict:
        return {"status": "SUCCESS", "job_url": job_url}

    async def take_screenshot(self, path: str = "screenshots/test.png") -> dict:
        if not self.manager.is_running:
            await self.manager.launch()
        page = await self.manager.get_page("default")
        await page.screenshot(path=path)
        return {"path": path}


playwright_engine = PlaywrightEngine()
