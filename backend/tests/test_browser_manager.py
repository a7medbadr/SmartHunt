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


@pytest.mark.asyncio
async def test_get_page_restores_saved_session_when_profile_exists(tmp_path, monkeypatch):
    """Regression test: a real login used to only live in this process's
    memory (browser.new_context() with no storage_state) — confirmed
    live 2026-08-03 that every container restart (routine, happens many
    times a session during deploys) silently logged the owner out,
    forcing a fresh LinkedIn login and real credentials every time,
    which was also triggering LinkedIn's own repeated-login abuse
    detection. A saved profile file must now be loaded automatically."""
    from smarthunt.browser.playwright import manager as manager_module

    monkeypatch.setattr(manager_module, "BROWSER_PROFILES_DIR", tmp_path)

    profile_file = tmp_path / "linkedin.json"
    profile_file.write_text('{"cookies": [], "origins": []}')

    manager = BrowserManager()
    manager.contexts = {}
    manager.pages = {}

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(
        return_value=AsyncMock(is_closed=MagicMock(return_value=False))
    )
    mock_context.set_default_timeout = MagicMock()
    mock_context.set_default_navigation_timeout = MagicMock()

    manager.browser = AsyncMock()
    manager.browser.new_context = AsyncMock(return_value=mock_context)

    await manager.get_page("linkedin")

    call_kwargs = manager.browser.new_context.call_args.kwargs
    assert call_kwargs.get("storage_state") == str(profile_file)


@pytest.mark.asyncio
async def test_get_page_skips_storage_state_when_no_saved_profile(tmp_path, monkeypatch):
    from smarthunt.browser.playwright import manager as manager_module

    monkeypatch.setattr(manager_module, "BROWSER_PROFILES_DIR", tmp_path)

    manager = BrowserManager()
    manager.contexts = {}
    manager.pages = {}

    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(
        return_value=AsyncMock(is_closed=MagicMock(return_value=False))
    )
    mock_context.set_default_timeout = MagicMock()
    mock_context.set_default_navigation_timeout = MagicMock()

    manager.browser = AsyncMock()
    manager.browser.new_context = AsyncMock(return_value=mock_context)

    await manager.get_page("linkedin")

    call_kwargs = manager.browser.new_context.call_args.kwargs
    assert "storage_state" not in call_kwargs


@pytest.mark.asyncio
async def test_save_state_writes_profile_file(tmp_path, monkeypatch):
    from smarthunt.browser.playwright import manager as manager_module

    monkeypatch.setattr(manager_module, "BROWSER_PROFILES_DIR", tmp_path)

    manager = BrowserManager()
    mock_context = AsyncMock()
    manager.contexts = {"linkedin": mock_context}

    await manager.save_state("linkedin")

    mock_context.storage_state.assert_awaited_once_with(path=str(tmp_path / "linkedin.json"))


@pytest.mark.asyncio
async def test_save_state_is_noop_for_unknown_provider(tmp_path, monkeypatch):
    from smarthunt.browser.playwright import manager as manager_module

    monkeypatch.setattr(manager_module, "BROWSER_PROFILES_DIR", tmp_path)

    manager = BrowserManager()
    manager.contexts = {}

    # Must not raise even though "linkedin" was never opened.
    await manager.save_state("linkedin")


@pytest.mark.asyncio
async def test_close_saves_state_for_every_named_context(tmp_path, monkeypatch):
    from smarthunt.browser.playwright import manager as manager_module

    monkeypatch.setattr(manager_module, "BROWSER_PROFILES_DIR", tmp_path)

    manager = BrowserManager()

    mock_page = AsyncMock()
    mock_page.is_closed = MagicMock(return_value=False)

    mock_context = AsyncMock()

    manager.pages = {"linkedin": mock_page}
    manager.contexts = {"linkedin": mock_context}
    manager.browser = AsyncMock()
    manager.playwright = AsyncMock()

    await manager.close()

    mock_context.storage_state.assert_awaited_once_with(path=str(tmp_path / "linkedin.json"))
