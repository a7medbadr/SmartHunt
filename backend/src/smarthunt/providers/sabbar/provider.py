import logging

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job

logger = logging.getLogger("smarthunt.providers.sabbar")

BASE_URL = "https://sabbar.com/en/jobs"

# Sabbar's own search box is a JS combobox (Ant Design Select, not a
# plain <input> the URL's query string drives) — there's no simple
# "?keyword=..." that actually filters results (confirmed live
# 2026-08-03: it silently ignored one). Rather than automate the
# combobox UI (type -> wait for suggestion dropdown -> click), this
# fetches Sabbar's own recent/unfiltered job listing across a few pages
# and lets DiscoveryService's own title-relevance filter
# (matching/services/job_relevance.py) do the actual keyword filtering
# — the same filter every other provider's results already pass
# through, so this isn't a weaker guarantee, just a different way of
# getting jobs in front of it.
PAGES_TO_FETCH = 3


class SabbarProvider(BaseProvider):

    name = "sabbar"

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
            logger.exception("sabbar_search_browser_unavailable")
            return []

        jobs: list[Job] = []

        try:
            for fetch_page in range(1, PAGES_TO_FETCH + 1):
                if len(jobs) >= limit:
                    break

                url = f"{BASE_URL}?page={fetch_page}"

                await search_page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await search_page.wait_for_timeout(2000)

                cards = search_page.locator(".job-card")
                count = await cards.count()

                if count == 0:
                    break

                for i in range(count):
                    if len(jobs) >= limit:
                        break

                    card = cards.nth(i)

                    try:
                        title = (await card.locator("h2").inner_text()).strip()
                        company = (
                            await card.locator(
                                "div.flex.justify-between > div > p"
                            ).first.inner_text()
                        ).strip()
                        card_location = (
                            await card.locator("p.text-light.flex.items-center").nth(1).inner_text()
                        ).strip()
                        href = await card.locator("a").first.get_attribute("href")
                    except Exception:
                        # A single malformed card shouldn't fail the whole search.
                        continue

                    if not title or not href:
                        continue

                    full_url = href if href.startswith("http") else f"https://sabbar.com{href}"

                    jobs.append(
                        Job(
                            external_id=full_url.rsplit("id-", 1)[-1],
                            provider=self.name,
                            title=title,
                            company=company,
                            location=card_location or (location or "Saudi Arabia"),
                            url=full_url,
                            description="",
                            country="Saudi Arabia",
                        )
                    )

            logger.info(
                "sabbar_search_completed",
                extra={"query": query, "found": len(jobs)},
            )

            return jobs

        except Exception:
            logger.exception("sabbar_search_failed", extra={"query": query})
            return jobs

        finally:
            await context.close()
