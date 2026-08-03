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

    # This page's context is a persistent, named session the owner
    # explicitly wants kept alive across calls (not re-authenticated
    # every time) — confirmed live 2026-08-03: navigating an already
    # -authenticated session to /login doesn't show the login form at
    # all (LinkedIn redirects it elsewhere), so the old unconditional
    # goto-then-fill-the-form flow just timed out waiting for fields
    # that were never going to appear. Check the session is actually
    # live first.
    try:
        current_url = (page.url or "").lower()
        if "linkedin.com" in current_url and ("feed" in current_url or "/in/" in current_url):
            logger.info("Reusing already-authenticated LinkedIn session.")
            return {"status": "SUCCESS"}
    except Exception:
        pass

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
            # This is exactly the case where a human needs to approve a
            # push notification on their phone — found live 2026-08-03
            # that reporting MANUAL_REQUIRED after a token ~2s check was
            # too eager: the owner hadn't had time to even see the
            # notification yet, and a second call to re-check status
            # would re-submit credentials and disrupt the pending
            # approval instead of just checking it. Poll the same page
            # for up to ~100s before giving up, so one call can actually
            # see a real, timely approval land.
            logger.warning("Manual verification required, polling for approval...")
            for _ in range(20):
                await page.wait_for_timeout(5000)
                current_url = page.url.lower()
                if "feed" in current_url or "/in/" in current_url:
                    logger.info("LinkedIn login successful after manual approval.")
                    return {"status": "SUCCESS"}
                if not any(marker in current_url for marker in MANUAL_REQUIRED_URL_MARKERS):
                    break
            else:
                return {"status": "MANUAL_REQUIRED"}

        # Found live 2026-08-03: page.content() can race an in-flight
        # navigation right after submit/approval ("Unable to retrieve
        # content because the page is navigating"), which isn't a real
        # login failure — just a transient timing issue. One short
        # retry resolves it.
        try:
            content = (await page.content()).lower()
        except Exception:
            await page.wait_for_timeout(1500)
            try:
                content = (await page.content()).lower()
            except Exception:
                content = ""

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
