import logging

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from smarthunt.core.config import settings

logger = logging.getLogger(__name__)

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"

MANUAL_REQUIRED_URL_MARKERS = (
    "checkpoint",
    "challenge",
)

MANUAL_REQUIRED_CONTENT_MARKERS = (
    "captcha",
    "verify",
    "two-step verification",
    "security check",
)


async def linkedin_login(page: Page) -> dict:
    """
    Perform LinkedIn login using credentials from settings.

    Never attempts to bypass CAPTCHA, MFA or security checkpoints.
    """

    email = settings.linkedin_email
    password = settings.linkedin_password

    if not email or not password:
        logger.error("LinkedIn credentials are not configured.")
        return {"status": "FAILED"}

    try:
        logger.info("Opening LinkedIn login page...")

        await page.goto(
            LINKEDIN_LOGIN_URL,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        await page.wait_for_selector("#username", timeout=30000)
        await page.wait_for_selector("#password", timeout=30000)

        logger.info("Submitting LinkedIn credentials...")

        await page.fill("#username", email)
        await page.fill("#password", password)

        await page.click("button[type='submit']")

        await page.wait_for_load_state("domcontentloaded")

        current_url = page.url.lower()

        logger.info("Current URL after login: %s", current_url)

        if any(marker in current_url for marker in MANUAL_REQUIRED_URL_MARKERS):
            logger.warning("Manual verification required.")
            return {"status": "MANUAL_REQUIRED"}

        content = (await page.content()).lower()

        if any(marker in content for marker in MANUAL_REQUIRED_CONTENT_MARKERS):
            logger.warning("CAPTCHA / MFA detected.")
            return {"status": "MANUAL_REQUIRED"}

        if "feed" in current_url or "/in/" in current_url:
            logger.info("LinkedIn login successful.")
            return {"status": "SUCCESS"}

        logger.warning("Login finished but success conditions were not met.")
        return {"status": "FAILED"}

    except PlaywrightTimeoutError:
        logger.exception("Timed out while waiting for LinkedIn login page.")
        return {"status": "FAILED"}

    except Exception:
        logger.exception("Unexpected error during LinkedIn login.")
        return {"status": "FAILED"}
