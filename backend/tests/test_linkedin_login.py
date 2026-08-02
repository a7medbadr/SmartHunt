import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.providers.linkedin.login import linkedin_login


@pytest.fixture(autouse=True)
def linkedin_credentials(monkeypatch):
    monkeypatch.setattr(
        "smarthunt.browser.providers.linkedin.login.settings.linkedin_email",
        "test@example.com",
    )
    monkeypatch.setattr(
        "smarthunt.browser.providers.linkedin.login.settings.linkedin_password",
        "secret",
    )


class FakeLocator:
    """Mimics the slice of Playwright's Locator API login.py uses.
    Real Locator.first/locator() are synchronous (return immediately);
    only actions like wait_for/fill/press are async — a plain AsyncMock
    page would make locator() itself async, which doesn't match reality."""

    def __init__(self):
        self.wait_for = AsyncMock()
        self.fill = AsyncMock()
        self.press = AsyncMock()

    @property
    def first(self):
        return self


def make_mock_page(url: str, content: str = "<html></html>"):
    page = AsyncMock()
    page.goto = AsyncMock()
    page.locator = MagicMock(return_value=FakeLocator())
    page.wait_for_load_state = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.url = url
    page.content = AsyncMock(return_value=content)
    return page


@pytest.mark.asyncio
async def test_login_success():
    page = make_mock_page("https://www.linkedin.com/feed/")

    result = await linkedin_login(page)

    assert result == {"status": "SUCCESS"}


@pytest.mark.asyncio
async def test_login_clicks_sign_in_button_as_enter_fallback():
    """Regression test: Enter-in-password-field (this module's original
    fix for LinkedIn's JS-driven, non-submit button) stopped reliably
    triggering the real submit as of 2026-08 — confirmed live, the page
    just sat on /login with the form filled in and no navigation at
    all. login() must also click the actual sign-in button (the last
    visible <button> — Apple SSO renders first) so submission still
    happens even when Enter alone is a no-op."""

    page = make_mock_page("https://www.linkedin.com/feed/")

    button_locator = MagicMock()
    button_locator.count = AsyncMock(return_value=2)
    sign_in_button = MagicMock()
    sign_in_button.click = AsyncMock()
    button_locator.nth = MagicMock(return_value=sign_in_button)

    field_locator = page.locator.return_value

    def locator_side_effect(selector, *args, **kwargs):
        if selector == "button:visible":
            return button_locator
        return field_locator

    page.locator = MagicMock(side_effect=locator_side_effect)

    result = await linkedin_login(page)

    assert result == {"status": "SUCCESS"}
    button_locator.nth.assert_called_once_with(1)
    sign_in_button.click.assert_awaited_once()


@pytest.mark.asyncio
async def test_login_manual_required_on_checkpoint():
    page = make_mock_page("https://www.linkedin.com/checkpoint/challenge")

    result = await linkedin_login(page)

    assert result == {"status": "MANUAL_REQUIRED"}


@pytest.mark.asyncio
async def test_login_manual_required_on_captcha_content():
    page = make_mock_page(
        "https://www.linkedin.com/login-submit",
        content="Please complete this security check (CAPTCHA)",
    )

    result = await linkedin_login(page)

    assert result == {"status": "MANUAL_REQUIRED"}


@pytest.mark.asyncio
async def test_login_failed_on_unexpected_page():
    page = make_mock_page("https://www.linkedin.com/login-error")

    result = await linkedin_login(page)

    assert result == {"status": "FAILED"}


@pytest.mark.asyncio
async def test_login_failed_without_credentials(monkeypatch):
    monkeypatch.setattr("smarthunt.browser.providers.linkedin.login.settings.linkedin_email", None)

    page = make_mock_page("https://www.linkedin.com/feed/")

    result = await linkedin_login(page)

    assert result == {"status": "FAILED"}


@pytest.mark.asyncio
async def test_login_failed_on_exception():
    page = make_mock_page("https://www.linkedin.com/feed/")
    page.goto = AsyncMock(side_effect=Exception("network error"))

    result = await linkedin_login(page)

    assert result == {"status": "FAILED"}
