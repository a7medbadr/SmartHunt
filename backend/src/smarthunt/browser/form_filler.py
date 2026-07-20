from __future__ import annotations

from playwright.async_api import Locator, Page

from smarthunt.browser.question_answerer import (
    Decision,
    question_answerer,
)
from smarthunt.browser.unknown_questions import (
    UnknownQuestionRecord,
    unknown_question_repository,
)
from smarthunt.domain import ResumeProfile
from smarthunt.logging.logger import logger


class FormFiller:
    """
    Generic browser form filler.

    Responsible only for:
    - reading form questions
    - asking QuestionAnswerer
    - filling Playwright locators

    It contains no profile mapping logic.
    """

    def __init__(
        self,
        page: Page,
        profile: ResumeProfile,
        provider: str = "unknown",
    ):
        self.page = page
        self.profile = profile
        self.provider = provider

        self.filled_fields = 0
        self.unknown_questions: list[str] = []

    async def fill_input(
        self,
        locator: Locator,
        question: str,
    ) -> bool:

        decision = question_answerer.answer(
            question,
            self.profile,
        )

        if decision.decision == Decision.ANSWER:
            await locator.fill(
                decision.answer
            )

            self.filled_fields += 1

            return True

        self.unknown_questions.append(
            question
        )

        await self._save_unknown_question(
            locator,
            question,
            decision,
        )

        return False

    async def _save_unknown_question(
        self,
        locator: Locator,
        question: str,
        decision,
    ) -> None:

        html = ""

        try:
            html = await locator.evaluate(
                "el => el.outerHTML"
            )
        except Exception:
            html = ""

        await unknown_question_repository.save(
            UnknownQuestionRecord(
                provider=self.provider,
                url=getattr(self.page, "url", "unknown"),
                label=question,
                html=html,
                confidence=decision.confidence,
            )
        )

        logger.info(
            f"UnknownQuestion provider={self.provider} "
            f"label={question} decision={decision.decision.value} "
            f"reason={decision.reason}"
        )

    async def fill_textareas(self):

        selectors = [
            "textarea",
            "input[type=text]",
            "input[type=email]",
            "input[type=tel]",
        ]

        for selector in selectors:

            await self._fill_selector(
                selector
            )

        return {
            "filled_fields": self.filled_fields,
            "unknown_questions": self.unknown_questions,
        }

    async def _fill_selector(
        self,
        selector: str,
    ):

        locators = await self.page.locator(
            selector
        ).all()

        for locator in locators:

            question = await self._extract_question(
                locator
            )

            if not question:
                continue

            await self.fill_input(
                locator,
                question,
            )

    async def _extract_question(
        self,
        locator: Locator,
    ) -> str:

        for attribute in (
            "aria-label",
            "placeholder",
            "name",
        ):

            value = await locator.get_attribute(
                attribute
            )

            if value:
                return value

        return ""
