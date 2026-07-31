from dataclasses import dataclass
from typing import Optional

from playwright.async_api import Page

FORM_SELECTORS = (
    ("easy_apply", "button[aria-label='Easy Apply']"),
    ("easy_apply", "text=Easy Apply"),
    ("apply_now", "text=Apply Now"),
    ("continue", "text=Continue"),
    ("submit", "text=Submit Application"),
)


@dataclass(slots=True)
class ApplicationForm:
    available: bool
    easy_apply: bool = False
    selector: Optional[str] = None


class FormDetector:
    async def detect(self, page: Page) -> ApplicationForm:
        for kind, selector in FORM_SELECTORS:
            try:
                element = await page.query_selector(selector)

                if element is not None:
                    return ApplicationForm(
                        available=True,
                        easy_apply=(kind == "easy_apply"),
                        selector=selector,
                    )

            except Exception:
                continue

        return ApplicationForm(
            available=False,
        )


form_detector = FormDetector()
