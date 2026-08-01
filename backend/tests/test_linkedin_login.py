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
