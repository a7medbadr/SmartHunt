import pytest
from unittest.mock import AsyncMock, MagicMock
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from smarthunt.browser.navigation import (
    JobPageNotFound,
    NavigationService,
)


def make_page(
    url: str = "https://www.linkedin.com/jobs/view/123",
):
    page = AsyncMock()

    page.url = url
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.title = AsyncMock(return_value="Linux Engineer")
    page.query_selector = AsyncMock(return_value=MagicMock())

    return page


@pytest.mark.asyncio
async def test_goto_job_success():
    page = make_page()

    service = NavigationService()

    await service.goto_job(
        page,
        "https://example.com/job/1",
    )

    page.goto.assert_called_once()


@pytest.mark.asyncio
async def test_goto_job_retry():
    page = make_page()

    page.goto = AsyncMock(
        side_effect=[
            PlaywrightTimeoutError("timeout"),
            None,
        ]
    )

    service = NavigationService()

    await service.goto_job(
        page,
        "https://example.com/job/1",
    )

    assert page.goto.call_count == 2


@pytest.mark.asyncio
async def test_wait_until_loaded_waits_for_domcontentloaded_and_networkidle():
    """Regression test: LinkedIn's job page is a heavy client-rendered
    SPA — the real Easy Apply button only appears after JS hydration,
    which domcontentloaded alone doesn't wait for. Confirmed live
    2026-08-03: a button scan right after domcontentloaded caught the
    page mid-hydration (generic "Apply" text, a stray logged-out
    widget) even on an authenticated session. Must also wait for
    networkidle (best-effort, non-fatal on timeout) before callers
    scan the DOM for interactive elements."""
    page = make_page()

    service = NavigationService()

    await service.wait_until_loaded(page)

    assert page.wait_for_load_state.call_count == 2
    waited_for = [call.args[0] for call in page.wait_for_load_state.call_args_list]
    assert waited_for == ["domcontentloaded", "networkidle"]


@pytest.mark.asyncio
async def test_wait_until_loaded_tolerates_networkidle_timeout():
    """A page that never goes fully idle (e.g. LinkedIn keeping a
    background connection open) must not fail the whole navigation —
    networkidle is a best-effort hydration window, not a hard
    requirement."""
    page = make_page()
    page.wait_for_load_state = AsyncMock(side_effect=[None, PlaywrightTimeoutError("timeout")])

    service = NavigationService()

    await service.wait_until_loaded(page)


@pytest.mark.asyncio
async def test_verify_job_page_success():
    page = make_page()

    service = NavigationService()

    await service.verify_job_page(page)


@pytest.mark.asyncio
async def test_verify_job_page_login():
    page = make_page("https://www.linkedin.com/login")

    service = NavigationService()

    with pytest.raises(JobPageNotFound):
        await service.verify_job_page(page)


@pytest.mark.asyncio
async def test_verify_job_page_404():
    page = make_page("https://www.linkedin.com/404")

    service = NavigationService()

    with pytest.raises(JobPageNotFound):
        await service.verify_job_page(page)


@pytest.mark.asyncio
async def test_verify_job_page_access_denied():
    page = make_page("https://www.linkedin.com/access-denied")

    service = NavigationService()

    with pytest.raises(JobPageNotFound):
        await service.verify_job_page(page)
