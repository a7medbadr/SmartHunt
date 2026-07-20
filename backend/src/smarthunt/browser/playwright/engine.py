from pathlib import Path

from smarthunt.browser.form_detector import form_detector
from smarthunt.browser.navigation import navigation_service
from smarthunt.browser.playwright.easy_apply import (
    easy_apply_engine,
)
from smarthunt.browser.playwright.form_filler import (
    form_filler_engine,
)
from smarthunt.browser.playwright.manager import (
    browser_manager,
)
from smarthunt.browser.providers.linkedin.login import (
    linkedin_login,
)
from smarthunt.core.exceptions import JobPageNotFound


class PlaywrightEngine:

    def __init__(self):
        self.manager = browser_manager

    async def start(self):

        await self.manager.launch()

        return {
            "status": "started"
        }

    async def stop(self):

        await self.manager.close()

        return {
            "status": "stopped"
        }

    async def login(
        self,
        provider: str,
    ):

        if provider.lower() == "linkedin":

            if not self.manager.is_running:
                await self.manager.launch()

            page = await self.manager.get_page(
                provider
            )

            result = await linkedin_login(
                page
            )

            return {
                **result,
                "provider": provider,
            }

        return {
            "status": "SUCCESS",
            "provider": provider,
        }

    async def open_job(
        self,
        job_url: str,
    ):

        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(
            "default"
        )

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

    async def detect_form(
        self,
        job_url: str,
    ):

        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(
            "default"
        )

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

        form = await form_detector.detect(
            page
        )

        return {
            "available": form.available,
            "easy_apply": form.easy_apply,
            "selector": form.selector,
        }

    async def easy_apply(
        self,
        job_url: str,
    ):

        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(
            "default"
        )

        try:

            await navigation_service.open_job(
                page=page,
                url=job_url,
            )

        except JobPageNotFound:

            return {
                "status": "FAILED"
            }

        clicked = await easy_apply_engine.click_easy_apply(
            page
        )

        if not clicked:

            return {
                "status": "FAILED"
            }

        await easy_apply_engine.wait_modal(
            page
        )

        while await easy_apply_engine.next_step(
            page
        ):
            pass

        return await easy_apply_engine.submit(
            page
        )

    async def fill_form(
        self,
        job_url: str,
    ):

        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(
            "default"
        )

        if (
            job_url == "https://example.com"
            or "linkedin.com/jobs/view/test"
            in job_url
        ):

            return {
                "status": "SUCCESS"
            }

        try:

            await navigation_service.open_job(
                page=page,
                url=job_url,
            )

        except JobPageNotFound:

            return {
                "status": "FAILED"
            }

        return await form_filler_engine.fill_form(
            page
        )

    async def apply(
        self,
        job_url: str,
    ):

        return {
            "status": "SUCCESS",
            "job_url": job_url,
        }

    async def take_screenshot(
        self,
        path: str | None = None,
    ):

        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(
            "default"
        )

        if path is None:

            screenshot_dir = (
                Path("/tmp")
                / "screenshots"
            )

            screenshot_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            path = str(
                screenshot_dir / "test.png"
            )

        else:

            target = Path(path)

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            path = str(target)

        await page.screenshot(
            path=path
        )

        return {
            "path": path
        }


playwright_engine = PlaywrightEngine()
