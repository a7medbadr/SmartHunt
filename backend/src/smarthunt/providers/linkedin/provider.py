import logging

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job

logger = logging.getLogger("smarthunt.providers.linkedin")

SEARCH_URL = "https://www.linkedin.com/jobs/search/"
RESULTS_PER_PAGE = 25


class LinkedInProvider(BaseProvider):

    name = "linkedin"

    supports_login = True
    supports_apply = True
    supports_resume_upload = True
    supports_cover_letter = True

    async def search(
        self,
        query=None,
        location=None,
        page=1,
        limit=25,
    ) -> list[Job]:
        """Scrapes LinkedIn's public job search (no login required for the
        first batch of results before LinkedIn's sign-in wall). Uses a
        dedicated isolated browser context so a concurrent call (e.g. a
        parallel discovery job, or a real login session elsewhere) can't
        race with this page's navigation."""

        effective_location = location or "Saudi Arabia"
        start = max(page, 1) - 1
        start *= RESULTS_PER_PAGE

        try:
            if not browser_manager.is_running:
                await browser_manager.launch()

            context, search_page = await browser_manager.new_isolated_page()
        except Exception:
            logger.exception("linkedin_search_browser_unavailable")
            return []

        try:
            url = (
                f"{SEARCH_URL}?keywords={query or ''}"
                f"&location={effective_location}&start={start}"
            )

            await search_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await search_page.wait_for_timeout(2000)

            cards = search_page.locator(".job-search-card")
            count = min(await cards.count(), limit)

            jobs: list[Job] = []

            for i in range(count):
                card = cards.nth(i)

                try:
                    title = (await card.locator(".base-search-card__title").inner_text()).strip()
                    company = (
                        await card.locator(".base-search-card__subtitle").inner_text()
                    ).strip()
                    card_location = (
                        await card.locator(".job-search-card__location").inner_text()
                    ).strip()
                    href = await card.locator("a.base-card__full-link").get_attribute("href")
                except Exception:
                    # A single malformed card shouldn't fail the whole search.
                    continue

                if not title or not href:
                    continue

                clean_url = href.split("?")[0]

                jobs.append(
                    Job(
                        external_id=clean_url.rsplit("-", 1)[-1],
                        provider=self.name,
                        title=title,
                        company=company,
                        location=card_location or effective_location,
                        url=clean_url,
                        description="",
                        country="Saudi Arabia",
                    )
                )

            logger.info(
                "linkedin_search_completed",
                extra={"query": query, "location": effective_location, "found": len(jobs)},
            )

            return jobs

        except Exception:
            logger.exception("linkedin_search_failed", extra={"query": query})
            return []

        finally:
            await context.close()
