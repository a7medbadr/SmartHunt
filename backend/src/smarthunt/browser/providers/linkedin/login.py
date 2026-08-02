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

    Selectors target stable HTML5 semantics (autocomplete attributes) and
    submit via Enter-in-password-field rather than a specific button
    selector/text, since LinkedIn's login page (as of 2026-08) renders
    the username/password field `id`s as per-request-random React IDs
    (e.g. `id="«R3jvtkejj35655j6»"`), serves the page in the visitor's
    detected locale (Arabic here), and its "submit" button is a plain
    `<button type="button">` driven by JS, not a real form submit —
    hardcoded `#username`/`#password`/`button[type='submit']` selectors
    time out against the real, current page.
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

        email_field = page.locator('input[autocomplete*="username"]:visible').first
        password_field = page.locator('input[autocomplete*="current-password"]:visible').first

        await email_field.wait_for(state="visible", timeout=30000)
        await password_field.wait_for(state="visible", timeout=30000)

        logger.info("Submitting LinkedIn credentials...")

        await email_field.fill(email)
        await password_field.fill(password)
        await password_field.press("Enter")

        # Enter-key submission (previously the reliable path — see the
        # module docstring) stopped consistently triggering the real
        # submit as of 2026-08: confirmed live, the page just sat on
        # /login with the form filled and no navigation. LinkedIn's
        # button is <button type="button"> with no stable id/name/type
        # to select by, so fall back to clicking the last visible
        # <button> on the page — confirmed live that this is the real
        # sign-in button (the Apple SSO button renders first). Harmless
        # if Enter already worked: by the time this runs the page has
        # already navigated away and this click becomes a no-op/timeout
        # that's swallowed below.
        try:
            buttons = page.locator("button:visible")
            count = await buttons.count()
            if count > 0:
                await buttons.nth(count - 1).click(timeout=5000)
        except Exception:
            logger.warning("Could not click LinkedIn sign-in button as Enter fallback.")

        try:
            await page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            pass

        await page.wait_for_timeout(2000)

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

        if "login" in current_url or "checkpoint" in current_url:
            logger.warning("Still on login/checkpoint page — credentials rejected.")
            return {"status": "FAILED"}

        logger.warning("Login finished but success conditions were not met.")
        return {"status": "MANUAL_REQUIRED"}

    except PlaywrightTimeoutError:
        logger.exception("Timed out while waiting for LinkedIn login page.")
        return {"status": "FAILED"}

    except Exception:
        logger.exception("Unexpected error during LinkedIn login.")
        return {"status": "FAILED"}
