from playwright.async_api import Page


class EasyApplyEngine:
    """
    LinkedIn Easy Apply automation engine.
    """

    async def click_easy_apply(self, page: Page) -> bool:
        selectors = [
            "button:has-text('Easy Apply')",
            "button:has-text('Apply')",
            "[aria-label='Easy Apply']",
        ]

        for selector in selectors:
            try:
                button = page.locator(selector).first

                if await button.count() > 0:
                    await button.click()
                    return True

            except Exception:
                continue

        return False

    async def wait_modal(self, page: Page) -> bool:
        selectors = [
            "div[role='dialog']",
            ".jobs-easy-apply-modal",
            "div:has-text('Contact info')",
        ]

        for selector in selectors:
            try:
                modal = page.locator(selector).first

                if await modal.count() > 0:
                    await modal.wait_for(timeout=10000)
                    return True

            except Exception:
                continue

        return False

    async def next_step(self, page: Page) -> bool:
        selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Continue applying')",
        ]

        for selector in selectors:
            try:
                button = page.locator(selector).first

                if await button.count() > 0:
                    await button.click()
                    await page.wait_for_timeout(1000)
                    return True

            except Exception:
                continue

        return False

    async def submit(self, page: Page) -> dict:
        content = (await page.content()).lower()

        if "application submitted" in content:
            return {
                "status": "SUCCESS"
            }

        if "save application" in content:
            return {
                "status": "REVIEW_REQUIRED"
            }

        selectors = [
            "button:has-text('Submit application')",
            "button:has-text('Submit')",
        ]

        for selector in selectors:
            try:
                button = page.locator(selector).first

                if await button.count() > 0:
                    await button.click()

                    await page.wait_for_timeout(2000)

                    content = (await page.content()).lower()

                    if "application submitted" in content:
                        return {
                            "status": "SUCCESS"
                        }

            except Exception:
                continue

        return {
            "status": "REVIEW_REQUIRED"
        }


    async def run(self, page: Page) -> dict:

        max_steps = 5
        steps = 0

        while steps < max_steps:

            moved = await self.next_step(page)

            if not moved:
                break

            steps += 1

        return await self.submit(page)


easy_apply_engine = EasyApplyEngine()
