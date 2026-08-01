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
    mock_page.wait_for_timeout = AsyncMock()

    mock_page.title = AsyncMock(return_value="Linux Engineer")

    mock_page.content = AsyncMock(return_value="<html></html>")

    mock_page.query_selector = AsyncMock(return_value=MagicMock())

    mock_page.url = "https://www.linkedin.com/feed/"

    locator = MagicMock()

    locator.get_attribute = AsyncMock(return_value="email")

    locator.fill = AsyncMock()

    mock_page.locator.return_value.all = AsyncMock(return_value=[locator])

    # linkedin_login() locates fields via `.first` (Playwright's real
    # Locator.first is sync, returns another Locator), then awaits
    # wait_for/fill/press on it.
    mock_page.locator.return_value.first = mock_page.locator.return_value
    mock_page.locator.return_value.wait_for = AsyncMock()
    mock_page.locator.return_value.fill = AsyncMock()
    mock_page.locator.return_value.press = AsyncMock()

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
    response = await client.post("/api/v1/browser/playwright/start")

    assert response.status_code == 200
    assert response.json()["status"] == "started"


@pytest.mark.asyncio
async def test_stop_engine(client: AsyncClient):
    await client.post("/api/v1/browser/playwright/start")

    response = await client.post("/api/v1/browser/playwright/stop")

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


@pytest.fixture
def mock_easy_apply_flow(monkeypatch):
    """apply() now really composes login -> open_job -> detect_form ->
    easy_apply (CLAUDE.md's "next step" for PlaywrightEngine.apply()).
    Mocked at the easy_apply_engine method level, same as
    test_easy_apply_application_status.py, rather than trying to thread a
    full Easy Apply modal interaction through the raw Playwright mock."""

    async def fake_click_easy_apply(page):
        return True

    async def fake_wait_modal(page):
        return True

    async def fake_run(page):
        return {"status": "SUCCESS"}

    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.easy_apply_engine.click_easy_apply",
        fake_click_easy_apply,
    )
    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.easy_apply_engine.wait_modal",
        fake_wait_modal,
    )
    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.easy_apply_engine.run",
        fake_run,
    )


@pytest.mark.asyncio
async def test_apply(client: AsyncClient, mock_easy_apply_flow):
    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "SUCCESS"
    assert data["job_url"] == "https://example.com/job/1"


@pytest.mark.asyncio
async def test_apply_fails_when_login_fails(client: AsyncClient, monkeypatch):
    async def fake_login(page):
        return {"status": "FAILED"}

    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.linkedin_login",
        fake_login,
    )

    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "FAILED"
    assert data["reason"] == "login_failed"


@pytest.mark.asyncio
async def test_apply_stops_for_manual_required_login(client: AsyncClient, monkeypatch):
    """CAPTCHA/MFA is one of the two cases that should ever pause instead
    of just failing — apply() must surface MANUAL_REQUIRED as-is, not
    flatten it into a generic FAILED."""

    async def fake_login(page):
        return {"status": "MANUAL_REQUIRED"}

    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.linkedin_login",
        fake_login,
    )

    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "MANUAL_REQUIRED"


@pytest.mark.asyncio
async def test_apply_fails_when_job_page_unavailable(client: AsyncClient, monkeypatch):
    from smarthunt.core.exceptions import JobPageNotFound

    async def fake_open_job(page, url):
        raise JobPageNotFound("gone")

    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.navigation_service.open_job",
        fake_open_job,
    )

    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "FAILED"
    assert data["reason"] == "job_page_unavailable"


@pytest.mark.asyncio
async def test_apply_fails_when_no_application_form(client: AsyncClient, monkeypatch):
    from smarthunt.browser.form_detector import ApplicationForm

    async def fake_detect(page):
        return ApplicationForm(available=False)

    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.form_detector.detect",
        fake_detect,
    )

    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "FAILED"
    assert data["reason"] == "no_application_form"


@pytest.mark.asyncio
async def test_apply_fails_for_external_ats_form(client: AsyncClient, monkeypatch):
    """A posting that only offers a "apply on employer site" form
    (external ATS like Greenhouse/Workday) should fail cleanly rather
    than mis-click through a form Easy Apply logic doesn't understand."""

    from smarthunt.browser.form_detector import ApplicationForm

    async def fake_detect(page):
        return ApplicationForm(available=True, easy_apply=False, selector="apply_now")

    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.form_detector.detect",
        fake_detect,
    )

    response = await client.post(
        "/api/v1/browser/playwright/apply",
        json={"job_url": "https://example.com/job/1"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "FAILED"
    assert data["reason"] == "external_ats_not_supported"


@pytest.mark.asyncio
async def test_screenshot(client: AsyncClient):
    response = await client.post("/api/v1/browser/playwright/screenshot")

    assert response.status_code == 200

    data = response.json()

    assert "path" in data

    assert data["path"].endswith("screenshots/test.png")


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
