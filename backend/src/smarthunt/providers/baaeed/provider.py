import logging

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job

logger = logging.getLogger("smarthunt.providers.baaeed")

SEARCH_URL = "https://baaeed.com/remote-jobs"

# Baaeed (baaeed.com, a Hsoub product) is a remote-work jobs board — no
# Cloudflare/bot wall, confirmed live 2026-08-03 scraping its real,
# unauthenticated listing page. Its own search box doesn't reliably
# filter by keyword either (same situation as Sabbar) — fetch the
# unfiltered recent listing and let DiscoveryService's own title
# relevance filter (matching/services/job_relevance.py) do the real
# filtering, same approach as sabbar/provider.py.
#
# Every job here is remote, not tied to a physical Saudi location —
# DiscoveryService's location filter (discovery/service.py) explicitly
# lets any job whose location contains "remote" through regardless of
# the Saudi-Arabia-only query, specifically so this provider isn't
# silently excluded from every scheduled run (fixed 2026-08-03, found
# while investigating why baaeed had produced zero real jobs despite
# real_discovery=True). Actual yield is still gated by the strict title
# relevance filter (matching/services/job_relevance.py) on top of
# that — baaeed's own listing skews toward sales/marketing/content
# roles, so a scheduled Linux/OpenShift/VMware/storage query will only
# occasionally match something real, which is expected, not a bug.


class BaaeedProvider(BaseProvider):

    name = "baaeed"

    supports_login = False
    supports_apply = False
    supports_resume_upload = False
    supports_cover_letter = False

    async def search(
        self,
        query=None,
        location=None,
        page=1,
        limit=25,
    ) -> list[Job]:
        try:
            if not browser_manager.is_running:
                await browser_manager.launch()

            context, search_page = await browser_manager.new_isolated_page()
        except Exception:
            logger.exception("baaeed_search_browser_unavailable")
            return []

        jobs: list[Job] = []

        try:
            await search_page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=30000)
            await search_page.wait_for_timeout(2000)

            cards = search_page.locator(".item__details")
            count = min(await cards.count(), limit)

            for i in range(count):
                card = cards.nth(i)

                try:
                    title = (await card.locator("h3.card-title a").inner_text()).strip()
                    href = await card.locator("h3.card-title a").get_attribute("href")
                    company = (
                        await card.locator("ul.baaeed-list__meta-items li")
                        .first.locator("a")
                        .inner_text()
                    ).strip()
                except Exception:
                    # A single malformed card shouldn't fail the whole search.
                    continue

                if not title or not href:
                    continue

                jobs.append(
                    Job(
                        external_id=href.rsplit("/", 1)[-1],
                        provider=self.name,
                        title=title,
                        company=company,
                        location="Remote",
                        url=href,
                        description="",
                        remote=True,
                    )
                )

            logger.info(
                "baaeed_search_completed",
                extra={"query": query, "found": len(jobs)},
            )

            return jobs

        except Exception:
            logger.exception("baaeed_search_failed", extra={"query": query})
            return jobs

        finally:
            await context.close()
