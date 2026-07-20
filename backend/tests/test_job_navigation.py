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
async def test_verify_job_page_success():
    page = make_page()

    service = NavigationService()

    await service.verify_job_page(page)


@pytest.mark.asyncio
async def test_verify_job_page_login():
    page = make_page(
        "https://www.linkedin.com/login"
    )

    service = NavigationService()

    with pytest.raises(JobPageNotFound):
        await service.verify_job_page(page)


@pytest.mark.asyncio
async def test_verify_job_page_404():
    page = make_page(
        "https://www.linkedin.com/404"
    )

    service = NavigationService()

    with pytest.raises(JobPageNotFound):
        await service.verify_job_page(page)


@pytest.mark.asyncio
async def test_verify_job_page_access_denied():
    page = make_page(
        "https://www.linkedin.com/access-denied"
    )

    service = NavigationService()

    with pytest.raises(JobPageNotFound):
        await service.verify_job_page(page)
