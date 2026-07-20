import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from smarthunt.browser.playwright.manager import BrowserManager


@pytest.mark.asyncio
async def test_launch_starts_browser():
    manager = BrowserManager()
    manager.browser = None
    manager.playwright = None
    manager.contexts = {}
    manager.pages = {}

    mock_browser = AsyncMock()
    mock_playwright_instance = AsyncMock()
    mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("smarthunt.browser.playwright.manager.async_playwright") as mock_ap:
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright_instance)
        await manager.launch()

    assert manager.browser is mock_browser
    assert manager.is_running is True


@pytest.mark.asyncio
async def test_launch_is_idempotent():
    manager = BrowserManager()
    existing_browser = AsyncMock()
    manager.browser = existing_browser

    with patch("smarthunt.browser.playwright.manager.async_playwright") as mock_ap:
        await manager.launch()

    mock_ap.assert_not_called()
    assert manager.browser is existing_browser


@pytest.mark.asyncio
async def test_get_page_creates_context_and_page_per_provider():
    manager = BrowserManager()
    manager.contexts = {}
    manager.pages = {}

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock()

    mock_page = AsyncMock()
    mock_page.is_closed = MagicMock(return_value=False)

    mock_context.new_page.return_value = mock_page
    mock_context.set_default_timeout = MagicMock()
    mock_context.set_default_navigation_timeout = MagicMock()

    manager.browser = AsyncMock()
    manager.browser.new_context = AsyncMock(return_value=mock_context)

    page = await manager.get_page("linkedin")

    assert page is mock_page
    assert "linkedin" in manager.contexts
    assert "linkedin" in manager.pages

    mock_context.set_default_timeout.assert_called_once()
    mock_context.set_default_navigation_timeout.assert_called_once()


@pytest.mark.asyncio
async def test_get_page_requires_running_browser():
    manager = BrowserManager()
    manager.browser = None

    with pytest.raises(RuntimeError):
        await manager.get_page("linkedin")


@pytest.mark.asyncio
async def test_close_shuts_down_browser_and_playwright():
    manager = BrowserManager()

    mock_page = AsyncMock()
    mock_page.is_closed = MagicMock(return_value=False)

    mock_context = AsyncMock()
    mock_browser = AsyncMock()
    mock_playwright = AsyncMock()

    manager.pages = {"linkedin": mock_page}
    manager.contexts = {"linkedin": mock_context}
    manager.browser = mock_browser
    manager.playwright = mock_playwright

    await manager.close()

    mock_page.close.assert_called_once()
    mock_context.close.assert_called_once()
    mock_browser.close.assert_called_once()
    mock_playwright.stop.assert_called_once()

    assert manager.browser is None
    assert manager.playwright is None
    assert manager.pages == {}
    assert manager.contexts == {}
