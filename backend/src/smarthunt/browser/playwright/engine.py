from pathlib import Path
import tempfile

from smarthunt.browser.form_detector import form_detector
from smarthunt.browser.navigation import navigation_service
from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.browser.providers.linkedin.login import linkedin_login
from smarthunt.core.exceptions import JobPageNotFound


class PlaywrightEngine:
    def __init__(self) -> None:
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

            return {
                **result,
                "provider": provider,
            }

        return {
            "status": "SUCCESS",
            "provider": provider,
        }

    async def open_job(self, job_url: str) -> dict:
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page("default")

        try:
            title = await navigation_service.open_job(
                page=page,
                url=job_url,
            )
        except JobPageNotFound:
            return {
                "status": "FAILED",
                "title": None,
            }

        return {
            "status": "SUCCESS",
            "title": title,
        }

    async def detect_form(self, job_url: str) -> dict:
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page("default")

        try:
            await navigation_service.open_job(
                page=page,
                url=job_url,
            )
        except JobPageNotFound:
            return {
                "available": False,
                "easy_apply": False,
                "selector": None,
            }

        form = await form_detector.detect(page)

        return {
            "available": form.available,
            "easy_apply": form.easy_apply,
            "selector": form.selector,
        }

    async def apply(self, job_url: str) -> dict:
        return {
            "status": "SUCCESS",
            "job_url": job_url,
        }

    async def take_screenshot(self, path: str | None = None) -> dict:
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page("default")

        if path is None:
            screenshot_dir = Path(tempfile.gettempdir()) / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            path = str(screenshot_dir / "test.png")
        else:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            path = str(target)

        await page.screenshot(path=path)

        return {
            "path": path,
        }


playwright_engine = PlaywrightEngine()
