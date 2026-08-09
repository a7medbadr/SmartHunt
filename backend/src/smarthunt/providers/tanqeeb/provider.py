import logging
from datetime import date, datetime
from urllib.parse import quote_plus, urljoin

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job

logger = logging.getLogger("smarthunt.providers.tanqeeb")

# saudi.tanqeeb.com is Tanqeeb's own Saudi-Arabia-scoped country subdomain
# (confirmed live 2026-08-06: every returned card carries
# data-job-country="Saudi") — no separate location filtering needed on our
# side the way LinkedIn's single global domain needs. country=54 is
# Tanqeeb's own internal id for Saudi Arabia (read off the site's own
# country <select>), kept explicit in case the subdomain alone isn't
# sufficient for some query shapes.
BASE_URL = "https://saudi.tanqeeb.com"
SAUDI_COUNTRY_ID = "54"
RESULTS_PER_PAGE = 20

# Each result is a real, server-rendered <article data-job-id="..."
# data-job-name="..." data-job-company="..." data-job-location="..."
# data-job-url="..." data-job-date="..." ...> — confirmed live: Tanqeeb
# aggregates postings from other boards too (data-job-source="Bayt" seen
# on real cards), but every card on this subdomain is genuinely Saudi
# regardless of source.
CARD_SELECTOR = "article[data-job-id]"

# The list card's own data-job-date is often relative ("6 hours ago",
# "Tuesday") rather than absolute, so it can't always be parsed into a
# real date — an unparseable date shouldn't fail the card, same as
# LinkedIn's posted_at handling.
DATE_FORMAT = "%d %B %Y"

# The job's own detail page has the real full description in this id —
# confirmed live 2026-08-06 (list cards only carry a short excerpt).
DESCRIPTION_SELECTOR = "#jobDescriptionBody"


class TanqeebProvider(BaseProvider):

    name = "tanqeeb"

    async def _fetch_description(self, page, url: str) -> str:
        """Visits a job's own detail page for its real description text —
        a second navigation per job, so failures here must never take down
        the whole search (an empty description just means that one job
        scores 0% on match)."""
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(1000)

            locator = page.locator(DESCRIPTION_SELECTOR).first
            if await locator.count() == 0:
                return ""

            return (await locator.inner_text()).strip()
        except Exception:
            logger.warning("tanqeeb_description_fetch_failed", extra={"url": url})
            return ""

    async def search(
        self,
        query=None,
        location=None,
        page=1,
        limit=25,
    ) -> list[Job]:
        """Scrapes Tanqeeb's public, server-rendered Saudi job search (no
        login required, no Cloudflare bot challenge encountered — unlike
        Bayt/GulfTalent/Wuzzuf). Uses a dedicated isolated browser context
        so a concurrent call can't race with this page's navigation."""

        page_num = max(page, 1)
        path = "/jobs/search" if page_num == 1 else f"/jobs/search/page/{page_num}"

        try:
            if not browser_manager.is_running:
                await browser_manager.launch()

            context, search_page = await browser_manager.new_isolated_page()
        except Exception:
            logger.exception("tanqeeb_search_browser_unavailable")
            return []

        try:
            url = (
                f"{BASE_URL}{path}?keywords={quote_plus(query or '')}"
                f"&country={SAUDI_COUNTRY_ID}"
            )

            await search_page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await search_page.wait_for_timeout(2000)

            cards = search_page.locator(CARD_SELECTOR)
            count = min(await cards.count(), limit)

            # Pass 1: collect every card's basic info first — same reason
            # as LinkedIn's provider: navigating search_page away to fetch
            # a description (pass 2) would make this locator stale for
            # any card not yet read.
            card_infos: list[dict] = []

            for i in range(count):
                card = cards.nth(i)

                try:
                    job_id = await card.get_attribute("data-job-id")
                    title = await card.get_attribute("data-job-name")
                    company = await card.get_attribute("data-job-company")
                    card_location = await card.get_attribute("data-job-location")
                    href = await card.get_attribute("data-job-url")
                    raw_date = await card.get_attribute("data-job-date")
                except Exception:
                    # A single malformed card shouldn't fail the whole search.
                    continue

                if not job_id or not title or not href:
                    continue

                # Tanqeeb's own data-job-location shorthands the country
                # as "Saudi" (e.g. "Saudi - Al Damam"), not "Saudi Arabia"
                # — DiscoveryService.discover()'s Saudi-only filter does a
                # substring check for "saudi arabia" in job.location, so
                # left as-is every Tanqeeb job would silently get dropped
                # from real discovery runs despite this subdomain only
                # ever returning genuine Saudi jobs (confirmed live
                # 2026-08-06: every card carries data-job-country="Saudi").
                if (
                    card_location
                    and card_location.lower().startswith("saudi")
                    and "saudi arabia" not in card_location.lower()
                ):
                    card_location = "Saudi Arabia" + card_location[len("Saudi") :]

                posted_at: date | None = None
                if raw_date:
                    try:
                        posted_at = datetime.strptime(raw_date, DATE_FORMAT).date()
                    except ValueError:
                        # Relative dates ("6 hours ago", "Tuesday") aren't
                        # parseable — posted_at is a nice-to-have, not
                        # required.
                        pass

                card_infos.append(
                    {
                        "id": job_id,
                        "title": title,
                        "company": company or "",
                        "location": card_location or location or "Saudi Arabia",
                        "url": urljoin(BASE_URL, href),
                        "posted_at": posted_at,
                    }
                )

            # Pass 2: visit each job's own detail page for its real
            # description — the list card only ever has a truncated
            # excerpt (see DESCRIPTION_SELECTOR's comment above).
            jobs: list[Job] = []

            for info in card_infos:
                description = await self._fetch_description(search_page, info["url"])

                jobs.append(
                    Job(
                        external_id=info["id"],
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
                "tanqeeb_search_completed",
                extra={"query": query, "found": len(jobs)},
            )

            return jobs

        except Exception:
            logger.exception("tanqeeb_search_failed", extra={"query": query})
            return []

        finally:
            await context.close()
