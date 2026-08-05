import pytest

from unittest.mock import AsyncMock, MagicMock

from smarthunt.browser.form_filler import FormFiller
from smarthunt.domain import ResumeProfile


def build_page(locator_groups):

    page = MagicMock()
    page.url = "https://example.com/job/test"

    page.locator.side_effect = [
        MagicMock(all=AsyncMock(return_value=group)) for group in locator_groups
    ]

    return page


@pytest.mark.asyncio
async def test_fill_email_success():

    locator = MagicMock()

    locator.fill = AsyncMock()

    locator.get_attribute = AsyncMock(return_value="email")

    page = build_page(
        [
            [locator],
            [],
            [],
            [],
        ]
    )

    filler = FormFiller(
        page=page,
        profile=ResumeProfile(email="test@example.com"),
    )

    result = await filler.fill_textareas()

    assert result["filled_fields"] == 1
    assert result["unknown_questions"] == []

    locator.fill.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_unknown_question():

    locator = MagicMock()

    locator.get_attribute = AsyncMock(return_value="security clearance")

    page = build_page(
        [
            [locator],
            [],
            [],
            [],
        ]
    )

    filler = FormFiller(
        page=page,
        profile=ResumeProfile(),
    )

    result = await filler.fill_textareas()

    assert result["filled_fields"] == 0

    assert result["unknown_questions"] == ["security clearance"]


@pytest.mark.asyncio
async def test_empty_page():

    page = build_page(
        [
            [],
            [],
            [],
            [],
        ]
    )

    filler = FormFiller(
        page=page,
        profile=ResumeProfile(),
    )

    result = await filler.fill_textareas()

    assert result["filled_fields"] == 0
    assert result["unknown_questions"] == []


@pytest.mark.asyncio
async def test_multiple_inputs():

    email = MagicMock()
    phone = MagicMock()

    email.get_attribute = AsyncMock(return_value="email")

    phone.get_attribute = AsyncMock(return_value="phone")

    email.fill = AsyncMock()
    phone.fill = AsyncMock()

    page = build_page(
        [
            [
                email,
                phone,
            ],
            [],
            [],
            [],
        ]
    )

    filler = FormFiller(
        page=page,
        profile=ResumeProfile(
            email="test@example.com",
            phone="+966500000000",
        ),
    )

    result = await filler.fill_textareas()

    assert result["filled_fields"] == 2
    assert result["unknown_questions"] == []

    email.fill.assert_awaited_once_with("test@example.com")

    phone.fill.assert_awaited_once_with("+966500000000")
