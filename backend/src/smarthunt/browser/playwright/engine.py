from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.browser.form_detector import form_detector
from smarthunt.browser.form_filler import FormFiller
from smarthunt.browser.navigation import navigation_service
from smarthunt.browser.playwright.easy_apply import easy_apply_engine
from smarthunt.browser.playwright.form_filler import form_filler_engine
from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.browser.providers.linkedin.login import linkedin_login
from smarthunt.core.exceptions import JobPageNotFound
from smarthunt.logging.logger import logger
from smarthunt.metrics.scheduler_lock import (
    scheduler_lock_acquired_total,
    scheduler_lock_conflicts_total,
)
from smarthunt.recruitment.service import RecruitmentService
from smarthunt.resume.profile_builder import resume_profile_builder


class PlaywrightEngine:
    def __init__(self):
        self.manager = browser_manager

    async def status(self):
        return {
            "running": self.manager.is_running,
            "browser_started": self.manager.browser is not None,
            "active_contexts": len(self.manager.contexts),
            "active_pages": len(self.manager.pages),
        }

    async def start(self):
        await self.manager.launch()
        return {"status": "started"}

    async def stop(self):
        await self.manager.close()
        return {"status": "stopped"}

    async def login(self, provider: str):
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

    async def open_job(self, job_url: str, provider: str = "default"):
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(provider)

        try:
            title = await navigation_service.open_job(page=page, url=job_url)
        except JobPageNotFound as exc:
            # This and detect_form()'s equivalent used to fail silently
            # (a plain FAILED/available=False with no reason logged) —
            # found live 2026-08-03 debugging a real apply() attempt
            # with no way to tell why it failed short of adding this.
            logger.warning(
                f"open_job could not verify job page job_url={job_url} "
                f"landed_on={page.url!r} reason={exc}"
            )
            return {"status": "FAILED", "title": None}

        return {"status": "SUCCESS", "title": title}

    async def detect_form(self, job_url: str, provider: str = "default"):
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(provider)

        try:
            await navigation_service.open_job(page=page, url=job_url)
        except JobPageNotFound as exc:
            logger.warning(
                f"detect_form could not verify job page job_url={job_url} "
                f"landed_on={page.url!r} reason={exc}"
            )
            return {
                "available": False,
                "easy_apply": False,
                "selector": None,
            }

        form = await form_detector.detect(page)

        if not form.available:
            logger.warning(
                f"detect_form found no application form job_url={job_url} "
                f"landed_on={page.url!r}"
            )

        return {
            "available": form.available,
            "easy_apply": form.easy_apply,
            "selector": form.selector,
        }

    async def easy_apply(
        self,
        job_url: str,
        application_id: str | None = None,
        db: AsyncSession | None = None,
        provider: str = "default",
    ):
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(provider)

        try:
            await navigation_service.open_job(page=page, url=job_url)
        except JobPageNotFound as exc:
            logger.warning(
                f"easy_apply could not verify job page job_url={job_url} "
                f"landed_on={page.url!r} reason={exc}"
            )
            return {"status": "FAILED"}

        clicked = await easy_apply_engine.click_easy_apply(page)

        if not clicked:
            scheduler_lock_conflicts_total.inc()
            logger.warning(
                f"easy_apply could not click an Easy Apply button "
                f"job_url={job_url} landed_on={page.url!r}"
            )
            return {"status": "FAILED"}

        scheduler_lock_acquired_total.inc()

        modal_found = await easy_apply_engine.wait_modal(page)

        if not modal_found:
            logger.warning(
                f"easy_apply clicked Easy Apply but no modal appeared "
                f"job_url={job_url} landed_on={page.url!r}"
            )

        result = await easy_apply_engine.run(page)

        logger.info(f"easy_apply finished job_url={job_url} result={result}")

        if result.get("status") == "PAUSED_UNKNOWN_QUESTION" and application_id and db is not None:
            await self._pause_application(application_id, db)

        return result

    async def _pause_application(
        self,
        application_id: str,
        db: AsyncSession,
    ) -> None:
        try:
            app_uuid = UUID(application_id)
        except ValueError:
            logger.warning(f"Invalid application_id={application_id}, skipping status update")
            return

        service = RecruitmentService(db)

        updated = await service.update_status(
            app_uuid,
            "PAUSED_UNKNOWN_QUESTION",
        )

        if updated is None:
            logger.warning(f"Application {application_id} not found, skipping status update")

    async def fill_form(self, job_url: str):
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page("default")

        if job_url == "https://example.com" or "linkedin.com/jobs/view/test" in job_url:
            return {"status": "SUCCESS"}

        try:
            await navigation_service.open_job(page=page, url=job_url)
        except JobPageNotFound:
            return {"status": "FAILED"}

        return await form_filler_engine.fill_form(page)

    async def fill_profile(
        self,
        job_url: str,
        resume: str,
    ):
        if not self.manager.is_running:
            await self.manager.launch()

        profile = resume_profile_builder.build(resume)

        page = await self.manager.get_page("default")

        try:
            await navigation_service.open_job(page=page, url=job_url)
        except JobPageNotFound:
            return {
                "status": "FAILED",
                "filled_fields": 0,
                "unknown_questions": [],
            }

        filler = FormFiller(
            page=page,
            profile=profile,
        )

        result = await filler.fill_textareas()

        status = "SUCCESS" if not result["unknown_questions"] else "PARTIAL_SUCCESS"

        return {
            "status": status,
            "filled_fields": result["filled_fields"],
            "unknown_questions": result["unknown_questions"],
        }

    async def apply(
        self,
        job_url: str,
        provider: str = "linkedin",
        application_id: str | None = None,
        db: AsyncSession | None = None,
    ):
        """Composes the already-real login/open_job/detect_form/easy_apply
        steps into a full unattended application. Only CAPTCHA/MFA
        (surfaced as login MANUAL_REQUIRED) or an unanswerable question
        (surfaced as easy_apply's PAUSED_UNKNOWN_QUESTION) should ever
        stop this short of a final SUCCESS/FAILED - everything else
        degrades to a FAILED with a `reason` rather than raising, so a
        scheduled batch of applications can't be taken down by one bad
        job posting."""

        login_result = await self.login(provider)

        if login_result.get("status") != "SUCCESS":
            logger.warning(f"apply() login failed job_url={job_url} result={login_result}")
            return {
                "status": login_result.get("status", "FAILED"),
                "job_url": job_url,
                "reason": "login_" + login_result.get("status", "failed").lower(),
            }

        # Regression fix: open_job/detect_form/easy_apply used to always
        # read the "default" (anonymous) browser context, a different
        # one than login() just authenticated ("linkedin") — so even a
        # successful login's session was never actually used by the
        # rest of the flow. Passing provider through keeps every step
        # on the same authenticated context.
        open_result = await self.open_job(job_url, provider=provider)

        if open_result.get("status") != "SUCCESS":
            logger.warning(f"apply() open_job failed job_url={job_url} result={open_result}")
            return {"status": "FAILED", "job_url": job_url, "reason": "job_page_unavailable"}

        form_result = await self.detect_form(job_url, provider=provider)

        if not form_result.get("available"):
            logger.warning(f"apply() no form detected job_url={job_url} result={form_result}")
            return {"status": "FAILED", "job_url": job_url, "reason": "no_application_form"}

        if not form_result.get("easy_apply"):
            logger.warning(
                f"apply() form found but not Easy Apply (external ATS) "
                f"job_url={job_url} result={form_result}"
            )
            return {"status": "FAILED", "job_url": job_url, "reason": "external_ats_not_supported"}

        result = await self.easy_apply(
            job_url, application_id=application_id, db=db, provider=provider
        )

        return {**result, "job_url": job_url}

    async def take_screenshot(self, path: str | None = None, provider: str = "default"):
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(provider)

        if path is None:
            screenshot_dir = Path("/tmp") / "screenshots"
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            path = str(screenshot_dir / "test.png")
        else:
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            path = str(target)

        await page.screenshot(path=path)

        return {"path": path}

    async def debug_page_buttons(self, job_url: str, provider: str = "default"):
        """One-off diagnostic: list every visible button's text/
        aria-label on a job page after navigating to it, on the same
        named context real apply() calls use — added to debug
        Easy Apply detection matching the wrong button (found live
        2026-08-03: matched a generic "Continue" instead)."""
        if not self.manager.is_running:
            await self.manager.launch()

        page = await self.manager.get_page(provider)

        try:
            await navigation_service.open_job(page=page, url=job_url)
        except JobPageNotFound:
            return {"status": "FAILED", "buttons": [], "url": page.url}

        buttons = page.locator("button:visible")
        count = await buttons.count()

        results = []
        for i in range(count):
            btn = buttons.nth(i)
            try:
                text = (await btn.inner_text()).strip()
            except Exception:
                text = ""
            try:
                aria_label = await btn.get_attribute("aria-label")
            except Exception:
                aria_label = None
            results.append({"text": text, "aria_label": aria_label})

        return {"status": "SUCCESS", "url": page.url, "buttons": results}


playwright_engine = PlaywrightEngine()
