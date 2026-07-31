import pytest
from unittest.mock import AsyncMock

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


def make_mock_page(url: str, content: str = "<html></html>"):
    page = AsyncMock()
    page.goto = AsyncMock()
    page.fill = AsyncMock()
    page.click = AsyncMock()
    page.wait_for_load_state = AsyncMock()
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
