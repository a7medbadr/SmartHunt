import logging

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from smarthunt.core.exceptions import JobPageNotFound

logger = logging.getLogger(__name__)

JOB_PAGE_SELECTORS = (
    "text=Easy Apply",
    "text=Apply",
    ".jobs-description",
    "[data-test-job-description]",
)

LOGIN_URL_MARKERS = (
    "/login",
    "/checkpoint",
    "/authwall",
)

NOT_FOUND_URL_MARKERS = (
    "/404",
    "page-not-found",
)

ACCESS_DENIED_URL_MARKERS = (
    "access-denied",
    "/403",
)


class NavigationService:

    def __init__(
        self,
        navigation_timeout: int = 30000,
        retry_count: int = 1,
    ) -> None:

        self.navigation_timeout = navigation_timeout
        self.retry_count = retry_count

    async def goto_job(
        self,
        page: Page,
        url: str,
    ) -> None:

        attempts = self.retry_count + 1

        last_error = None

        for attempt in range(1, attempts + 1):

            try:

                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=self.navigation_timeout,
                )

                return

            except PlaywrightTimeoutError as exc:

                last_error = exc

                logger.warning(
                    "Navigation timeout (%s/%s): %s",
                    attempt,
                    attempts,
                    url,
                )

                if attempt < attempts:
                    continue

        if last_error:
            raise last_error

    async def wait_until_loaded(
        self,
        page: Page,
    ) -> None:

        try:

            await page.wait_for_load_state(
                "domcontentloaded",
                timeout=5000,
            )

        except PlaywrightTimeoutError:

            logger.warning("Timed out waiting for page load.")

    async def verify_job_page(
        self,
        page: Page,
    ) -> None:

        current_url = (page.url or "").lower()

        if any(marker in current_url for marker in LOGIN_URL_MARKERS):
            raise JobPageNotFound("Redirected to login page.")

        if any(marker in current_url for marker in NOT_FOUND_URL_MARKERS):
            raise JobPageNotFound("Job page not found.")

        if any(marker in current_url for marker in ACCESS_DENIED_URL_MARKERS):
            raise JobPageNotFound("Access denied.")

        for selector in JOB_PAGE_SELECTORS:

            try:

                element = await page.query_selector(selector)

                if element is not None:
                    return

            except Exception:

                logger.exception(
                    "Failed checking selector %s",
                    selector,
                )

        raise JobPageNotFound("Could not verify job page.")

    async def get_job_title(
        self,
        page: Page,
    ) -> str:

        try:
            return await page.title()

        except Exception:
            return ""

    async def open_job(
        self,
        page: Page,
        url: str,
    ) -> str:

        await self.goto_job(
            page,
            url,
        )

        await self.wait_until_loaded(
            page,
        )

        await self.verify_job_page(
            page,
        )

        return await self.get_job_title(
            page,
        )


navigation_service = NavigationService()
