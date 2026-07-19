from playwright.async_api import Page

from smarthunt.core.config import settings

MANUAL_REQUIRED_URL_MARKERS = ("checkpoint", "challenge")
MANUAL_REQUIRED_CONTENT_MARKERS = (
    "captcha",
    "verify",
    "two-step verification",
    "security check",
)


async def linkedin_login(page: Page) -> dict:
    """
    Logs into LinkedIn using credentials from settings (.env: LINKEDIN_EMAIL,
    LINKEDIN_PASSWORD). Never attempts to solve or bypass CAPTCHA/MFA/checkpoint
    challenges — if one is detected, it stops and reports MANUAL_REQUIRED so a
    human can intervene.
    """
    email = settings.linkedin_email
    password = settings.linkedin_password

    if not email or not password:
        return {"status": "FAILED"}

    try:
        await page.goto("https://www.linkedin.com/login", wait_until="networkidle")
        await page.fill("#username", email)
        await page.fill("#password", password)
        await page.click("button[type='submit']")
        await page.wait_for_load_state("networkidle")

        current_url = page.url

        if any(marker in current_url for marker in MANUAL_REQUIRED_URL_MARKERS):
            return {"status": "MANUAL_REQUIRED"}

        content = (await page.content()).lower()
        if any(marker in content for marker in MANUAL_REQUIRED_CONTENT_MARKERS):
            return {"status": "MANUAL_REQUIRED"}

        if "feed" in current_url or "/in/" in current_url:
            return {"status": "SUCCESS"}

        return {"status": "FAILED"}

    except Exception:
        return {"status": "FAILED"}
