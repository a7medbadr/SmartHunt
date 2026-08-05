import logging
from datetime import date

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job

logger = logging.getLogger("smarthunt.providers.linkedin")

SEARCH_URL = "https://www.linkedin.com/jobs/search/"
RESULTS_PER_PAGE = 25

# The search-results page card (.job-search-card) carries no description
# text at all — confirmed live 2026-08-03 inspecting its real markup,
# just title/company/location/posting-date — which is why every stored
# job's description/requirements were empty and match() (matching
# resume text against `f"{description} {requirements}"`) always scored
# 0% regardless of the actual resume. A job's own detail page IS
# viewable anonymously though (same as the search page itself — no
# LinkedIn sign-in wall), and has the real description in
# `.description__text`/`.show-more-less-html__markup`.
DESCRIPTION_SELECTOR = ".description__text, .show-more-less-html__markup"

# LinkedIn renamed this element's class from `.job-search-card__listdate`
# to `.job-search-card__listdate--new` at some point after 2026-07-20 (the
# original selector was confirmed live that day) — found 2026-08-04 after
# every single stored job had posted_at=None despite the extraction logic
# itself being correct and unit-tested; a live page dump showed the real
# markup is now `<time class="job-search-card__listdate--new" datetime="...">`.
# Matching both keeps this working if LinkedIn ever reverts or A/B tests it.
POSTED_DATE_SELECTOR = ".job-search-card__listdate, .job-search-card__listdate--new"


class LinkedInProvider(BaseProvider):

    name = "linkedin"

    supports_login = True
    supports_apply = True
    supports_resume_upload = True
    supports_cover_letter = True

    async def _fetch_description(self, page, url: str) -> str:
        """Visits a job's own detail page for its real description text
        — a second navigation per job, so failures here must never take
        down the whole search (an empty description just means that one
        job scores 0% on match, same as before this fix, not a crash)."""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1000)

            locator = page.locator(DESCRIPTION_SELECTOR).first
            if await locator.count() == 0:
                return ""

            return (await locator.inner_text()).strip()
        except Exception:
            logger.warning("linkedin_description_fetch_failed", extra={"url": url})
            return ""

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

            # Pass 1: collect every card's basic info first. Navigating
            # search_page away to fetch a description (pass 2 below)
            # would make the `cards` locator stale for any card not yet
            # read — all list-page reads have to happen before the first
            # navigation away from the search results page.
            card_infos: list[dict] = []

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

                posted_at: date | None = None
                try:
                    raw_date = await card.locator(POSTED_DATE_SELECTOR).first.get_attribute(
                        "datetime"
                    )
                    if raw_date:
                        posted_at = date.fromisoformat(raw_date)
                except Exception:
                    # Missing/unparseable posting date shouldn't fail the
                    # card — it's a nice-to-have, not required.
                    pass

                card_infos.append(
                    {
                        "title": title,
                        "company": company,
                        "location": card_location or effective_location,
                        "url": clean_url,
                        "posted_at": posted_at,
                    }
                )

            # Pass 2: visit each job's own detail page for its real
            # description — needed for match() to score against
            # anything real (see DESCRIPTION_SELECTOR's comment above).
            jobs: list[Job] = []

            for info in card_infos:
                description = await self._fetch_description(search_page, info["url"])

                jobs.append(
                    Job(
                        external_id=info["url"].rsplit("-", 1)[-1],
                        provider=self.name,
                        title=info["title"],
                        company=info["company"],
                        location=info["location"],
                        url=info["url"],
                        description=description,
                        country="Saudi Arabia",
                        posted_at=info["posted_at"],
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
