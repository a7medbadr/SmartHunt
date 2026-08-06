import pytest
from unittest.mock import MagicMock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.browser.playwright.manager import BrowserManager, browser_manager
from smarthunt.database.models.application import Application


@pytest.fixture(autouse=True)
def mock_browser_manager(monkeypatch):
    mock_page = MagicMock()
    mock_page.url = "https://www.linkedin.com/jobs/view/test"

    async def fake_launch(self, headless: bool = True):
        browser_manager.browser = MagicMock()

    async def fake_close(self):
        browser_manager.browser = None
        browser_manager.contexts.clear()
        browser_manager.pages.clear()

    async def fake_get_page(self, provider: str):
        return mock_page

    # Patch the class, not the singleton instance — patching the
    # instance permanently stamps these fakes onto it at monkeypatch
    # teardown (real methods currently resolve through the class), which
    # then silently shadows every later test's own class-level patch for
    # the rest of the suite run. See CLAUDE.md's "Test-suite gotcha" note.
    monkeypatch.setattr(BrowserManager, "launch", fake_launch)
    monkeypatch.setattr(BrowserManager, "close", fake_close)
    monkeypatch.setattr(BrowserManager, "get_page", fake_get_page)

    yield mock_page


@pytest.fixture(autouse=True)
def mock_navigation(monkeypatch):
    async def fake_open_job(page, url):
        return "Linux Engineer"

    monkeypatch.setattr(
        "smarthunt.browser.playwright.engine.navigation_service.open_job",
        fake_open_job,
    )


@pytest.fixture(autouse=True)
def mock_easy_apply_flow(monkeypatch):
    async def fake_click_easy_apply(page):
        return True

    async def fake_wait_modal(page):
        return True

    async def fake_run(page, job_id=None):
        return {
            "status": "PAUSED_UNKNOWN_QUESTION",
            "question": "years of kubernetes experience",
        }

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
async def test_easy_apply_updates_application_status(
    client: AsyncClient,
    db_session: AsyncSession,
):
    application = Application(
        job_title="Linux Engineer",
        company="Acme",
        url="https://www.linkedin.com/jobs/view/test",
        status="APPLIED",
    )

    db_session.add(application)
    await db_session.commit()
    await db_session.refresh(application)

    response = await client.post(
        "/api/v1/browser/playwright/easy-apply",
        json={
            "job_url": "https://www.linkedin.com/jobs/view/test",
            "application_id": str(application.id),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "PAUSED_UNKNOWN_QUESTION"
    assert data["question"] == "years of kubernetes experience"

    await db_session.refresh(application)

    assert application.status == "PAUSED_UNKNOWN_QUESTION"


@pytest.mark.asyncio
async def test_easy_apply_without_application_id_skips_db_update(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/browser/playwright/easy-apply",
        json={
            "job_url": "https://www.linkedin.com/jobs/view/test",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "PAUSED_UNKNOWN_QUESTION"


@pytest.mark.asyncio
async def test_easy_apply_invalid_application_id_does_not_error(
    client: AsyncClient,
):
    response = await client.post(
        "/api/v1/browser/playwright/easy-apply",
        json={
            "job_url": "https://www.linkedin.com/jobs/view/test",
            "application_id": "not-a-uuid",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "PAUSED_UNKNOWN_QUESTION"
