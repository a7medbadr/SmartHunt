import pytest
from unittest.mock import AsyncMock, MagicMock

from httpx import AsyncClient

from smarthunt.browser.playwright.manager import browser_manager


@pytest.fixture(autouse=True)
def mock_browser_manager(monkeypatch):
    mock_page = MagicMock()

    mock_page.goto = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.screenshot = AsyncMock()

    mock_page.wait_for_selector = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    mock_page.title = AsyncMock(
        return_value="Linux Engineer"
    )

    mock_page.content = AsyncMock(
        return_value="<html></html>"
    )

    mock_page.query_selector = AsyncMock(
        return_value=MagicMock()
    )

    mock_page.url = "https://www.linkedin.com/feed/"

    locator = MagicMock()

    locator.get_attribute = AsyncMock(
        return_value="email"
    )

    locator.fill = AsyncMock()

    mock_page.locator.return_value.all = AsyncMock(
        return_value=[
            locator
        ]
    )

    async def fake_launch(headless: bool = True):
        browser_manager.browser = MagicMock()

    async def fake_close():
        browser_manager.browser = None
        browser_manager.contexts.clear()
        browser_manager.pages.clear()

    async def fake_get_page(provider: str):
        return mock_page

    monkeypatch.setattr(
        browser_manager,
        "launch",
        fake_launch,
    )

    monkeypatch.setattr(
        browser_manager,
        "close",
        fake_close,
    )

    monkeypatch.setattr(
        browser_manager,
        "get_page",
        fake_get_page,
    )

    yield mock_page


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


@pytest.mark.asyncio
async def test_start_engine(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/start"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "started"


@pytest.mark.asyncio
async def test_stop_engine(client: AsyncClient):
    await client.post(
        "/api/v1/browser/playwright/start"
    )

    response = await client.post(
        "/api/v1/browser/playwright/stop"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "stopped"


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/login",
        json={"provider": "linkedin"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["provider"] == "linkedin"


@pytest.mark.asyncio
async def test_open_job(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/open-job",
        json={"job_url": "https://example.com/job"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["title"] == "Linux Engineer"


@pytest.mark.asyncio
async def test_detect_form(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/detect-form",
        json={"job_url": "https://example.com/job"},
    )

    assert response.status_code == 200

    data = response.json()

    assert "available" in data
    assert "easy_apply" in data


@pytest.mark.asyncio
async def test_apply(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["job_url"] == "https://example.com/job/1"


@pytest.mark.asyncio
async def test_screenshot(client: AsyncClient):
    response = await client.post(
        "/api/v1/browser/playwright/screenshot"
    )

    assert response.status_code == 200

    data = response.json()

    assert "path" in data

    assert data["path"].endswith(
        "screenshots/test.png"
    )


@pytest.mark.asyncio
async def test_fill_profile_success(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/browser/playwright/fill-profile",
        json={
            "job_url": "https://example.com/job",
            "resume": (
                "Email: test@example.com\n"
                "Phone: +966500000000\n"
                "5 years experience\n"
                "Python Linux OpenShift"
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "SUCCESS"


@pytest.mark.asyncio
async def test_fill_profile_unknown_questions(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/browser/playwright/fill-profile",
        json={
            "job_url": "https://example.com/job",
            "resume": "Email: test@example.com",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] in [
        "SUCCESS",
        "PARTIAL_SUCCESS",
    ]
