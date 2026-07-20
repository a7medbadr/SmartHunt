import pytest
from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.form_detector import FormDetector


def make_page(selector=None):
    page = AsyncMock()

    async def fake_query_selector(value):
        if selector == value:
            return MagicMock()
        return None

    page.query_selector = AsyncMock(
        side_effect=fake_query_selector
    )

    return page


@pytest.mark.asyncio
async def test_detect_easy_apply():
    detector = FormDetector()

    page = make_page(
        "button[aria-label='Easy Apply']"
    )

    result = await detector.detect(page)

    assert result.available is True
    assert result.easy_apply is True


@pytest.mark.asyncio
async def test_detect_apply_now():
    detector = FormDetector()

    page = make_page(
        "text=Apply Now"
    )

    result = await detector.detect(page)

    assert result.available is True
    assert result.easy_apply is False


@pytest.mark.asyncio
async def test_detect_no_form():
    detector = FormDetector()

    page = make_page()

    result = await detector.detect(page)

    assert result.available is False
    assert result.easy_apply is False
    assert result.selector is None
