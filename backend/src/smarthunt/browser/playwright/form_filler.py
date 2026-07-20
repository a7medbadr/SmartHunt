from pathlib import Path

from playwright.async_api import Page

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
        await page.locator(selector).fill(value)

    async def fill_textarea(
        self,
        page: Page,
        selector: str,
        value: str,
    ):
        await page.locator(selector).fill(value)

    async def fill_select(
        self,
        page: Page,
        selector: str,
        value: str,
    ):
        await page.locator(selector).select_option(value)

    async def fill_checkbox(
        self,
        page: Page,
        selector: str,
    ):
        checkbox = page.locator(selector)

        if not await checkbox.is_checked():
            await checkbox.check()

    async def fill_radio(
        self,
        page: Page,
        selector: str,
    ):
        await page.locator(selector).check()

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
            await page.locator(selector).set_input_files(
                str(path)
            )

    async def fill_form(
        self,
        page: Page,
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
                    await element.fill(
                        profile["email"]
                    )

                elif "phone" in field:
                    await element.fill(
                        profile["phone"]
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
                    await element.check()

            except Exception:
                continue

        unknown = await self.detect_unknown_question(
            page
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
                return question

        return None


form_filler_engine = FormFillerEngine()
