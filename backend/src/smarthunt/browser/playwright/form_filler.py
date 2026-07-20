from pathlib import Path

from playwright.async_api import Page

from smarthunt.browser.playwright.retry import retry_executor
from smarthunt.browser.question_classifier import (
    QuestionType,
    classify,
)
from smarthunt.browser.unknown_questions import (
    UnknownQuestionRecord,
    unknown_question_repository,
)
from smarthunt.logging.logger import logger
from smarthunt.resume.storage.storage import (
    resume_storage,
)


class FormFillerEngine:
    """
    Dynamic application form filling engine.
    """

    def get_profile(self) -> dict:
        info = resume_storage.get_resume_info()

        return {
            "first_name": "",
            "last_name": "",
            "email": "",
            "phone": "",
            "resume_path": (
                info["stored_path"]
                if info.get("uploaded")
                else None
            ),
        }

    async def fill_textbox(
        self,
        page: Page,
        selector: str,
        value: str,
    ):
        await retry_executor.run(
            page.locator(selector).fill,
            value,
            operation="fill",
            provider="linkedin",
            page_url=page.url,
        )

    async def fill_textarea(
        self,
        page: Page,
        selector: str,
        value: str,
    ):
        await retry_executor.run(
            page.locator(selector).fill,
            value,
            operation="fill",
            provider="linkedin",
            page_url=page.url,
        )

    async def fill_select(
        self,
        page: Page,
        selector: str,
        value: str,
    ):
        await retry_executor.run(
            page.locator(selector).select_option,
            value,
            operation="select_option",
            provider="linkedin",
            page_url=page.url,
        )

    async def fill_checkbox(
        self,
        page: Page,
        selector: str,
    ):
        checkbox = page.locator(selector)

        if not await checkbox.is_checked():
            await retry_executor.run(
                checkbox.check,
                operation="click",
                provider="linkedin",
                page_url=page.url,
            )

    async def fill_radio(
        self,
        page: Page,
        selector: str,
    ):
        await retry_executor.run(
            page.locator(selector).check,
            operation="click",
            provider="linkedin",
            page_url=page.url,
        )

    async def upload_resume(
        self,
        page: Page,
        selector: str,
        resume_path: str | None,
    ):

        if not resume_path:
            return

        path = Path(resume_path)

        if path.exists():
            await retry_executor.run(
                page.locator(selector).set_input_files,
                str(path),
                operation="fill",
                provider="linkedin",
                page_url=page.url,
            )

    async def fill_form(
        self,
        page: Page,
        provider: str = "linkedin",
    ) -> dict:

        profile = self.get_profile()

        inputs = await page.locator(
            "input, textarea, select"
        ).all()

        for element in inputs:

            try:
                input_type = await element.get_attribute("type")

                name = await element.get_attribute("name")

                placeholder = await element.get_attribute(
                    "placeholder"
                )

                field = (
                    name
                    or placeholder
                    or ""
                ).lower()

                if "email" in field:
                    await retry_executor.run(
                        element.fill,
                        profile["email"],
                        operation="fill",
                        provider=provider,
                        page_url=page.url,
                    )

                elif "phone" in field:
                    await retry_executor.run(
                        element.fill,
                        profile["phone"],
                        operation="fill",
                        provider=provider,
                        page_url=page.url,
                    )

                elif (
                    "resume" in field
                    and input_type == "file"
                ):

                    await self.upload_resume(
                        page,
                        "input[type='file']",
                        profile["resume_path"],
                    )

                elif input_type == "checkbox":
                    await retry_executor.run(
                        element.check,
                        operation="click",
                        provider=provider,
                        page_url=page.url,
                    )

            except Exception:
                continue

        unknown = await self.detect_unknown_question(
            page,
            provider=provider,
        )

        if unknown:
            return {
                "status": "QUESTION_REQUIRED",
                "question": unknown,
            }

        return {
            "status": "SUCCESS"
        }

    async def detect_unknown_question(
        self,
        page: Page,
        provider: str = "linkedin",
    ):

        questions = [
            "years of kubernetes experience",
            "years of experience",
            "authorization",
            "sponsorship",
        ]

        text = (
            await page.content()
        ).lower()

        for question in questions:
            if question in text:

                question_type = classify(question)

                await unknown_question_repository.save(
                    UnknownQuestionRecord(
                        provider=provider,
                        url=getattr(page, "url", "unknown"),
                        label=question,
                        html=text[:2000],
                        confidence=(
                            0.3
                            if question_type is QuestionType.UNKNOWN
                            else 0.6
                        ),
                    )
                )

                logger.info(
                    f"UnknownQuestion provider={provider} "
                    f"label={question} type={question_type.value}"
                )

                return question

        return None


form_filler_engine = FormFillerEngine()
