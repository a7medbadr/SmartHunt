import logging
import re
from datetime import date
from html import unescape

import httpx

from smarthunt.providers.base.provider import BaseProvider
from smarthunt.providers.models.job import Job

logger = logging.getLogger("smarthunt.providers.workable")

# jobs.workable.com is a real, unified search across every company that
# hosts its job board on Workable (an ATS) — unlike LinkedIn/Tanqeeb this
# needs no browser at all: the page's own SSR data is backed by a plain
# public JSON endpoint (confirmed live 2026-08-10, no auth/cookie/CSRF
# needed, no Cloudflare bot challenge encountered unlike Bayt/GulfTalent/
# Wuzzuf) that returns full descriptions in one call, so there's no
# second per-job detail-page pass like LinkedIn/Tanqeeb need.
API_URL = "https://jobs.workable.com/api/v1/jobs"

# The API 400s with {"limit":"Must be less than or equal to 20"} above
# this — confirmed live. Pagination beyond one page walks the response's
# own opaque `nextPageToken` cursor (not a page number).
MAX_PAGE_SIZE = 20

HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(raw: str | None) -> str:
    """Every text field in this API (description/requirementsSection/
    benefitsSection) is real HTML, not the plain text every other
    provider's inner_text()-based scrape already produces — strip tags
    so matching/AI prompts see the same shape of text as everywhere
    else, without pulling in a whole HTML-parsing dependency for it."""
    if not raw:
        return ""
    text = _TAG_RE.sub(" ", raw)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


class WorkableProvider(BaseProvider):

    name = "workable"

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
        effective_location = location or "Saudi Arabia"
        page_num = max(page, 1)
        skip = (page_num - 1) * MAX_PAGE_SIZE

        jobs: list[Job] = []

        try:
            async with httpx.AsyncClient(timeout=15.0, headers=HEADERS) as client:
                next_token: str | None = None

                # Walk the cursor forward to the requested page — in
                # practice every real caller here always asks for page 1
                # (see CLAUDE.md's provider notes), this just keeps the
                # `page` param honest rather than silently ignoring it.
                while skip > 0:
                    params: dict = {
                        "location": effective_location,
                        "limit": min(MAX_PAGE_SIZE, skip),
                    }
                    if query:
                        params["query"] = query
                    if next_token:
                        params["nextPageToken"] = next_token

                    resp = await client.get(API_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                    got = len(data.get("jobs", []))
                    next_token = data.get("nextPageToken")
                    skip -= got

                    if not next_token or got == 0:
                        break

                while len(jobs) < limit:
                    params = {
                        "location": effective_location,
                        "limit": min(MAX_PAGE_SIZE, limit - len(jobs)),
                    }
                    if query:
                        params["query"] = query
                    if next_token:
                        params["nextPageToken"] = next_token

                    resp = await client.get(API_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                    raw_jobs = data.get("jobs", [])
                    if not raw_jobs:
                        break

                    for raw in raw_jobs:
                        try:
                            job_id = raw["id"]
                            title = raw["title"]
                            href = raw["url"]
                        except (KeyError, TypeError):
                            # A single malformed entry shouldn't fail the
                            # whole search.
                            continue

                        if not job_id or not title or not href:
                            continue

                        company = (raw.get("company") or {}).get("title", "")

                        loc = raw.get("location") or {}
                        city = loc.get("city")
                        country_name = loc.get("countryName") or effective_location
                        job_location = f"{city}, {country_name}" if city else country_name

                        description = _strip_html(raw.get("description"))
                        requirements = _strip_html(raw.get("requirementsSection"))
                        full_description = (
                            f"{description}\n\n{requirements}".strip()
                            if requirements
                            else description
                        )

                        posted_at: date | None = None
                        raw_created = raw.get("created")
                        if raw_created:
                            try:
                                posted_at = date.fromisoformat(raw_created[:10])
                            except ValueError:
                                pass

                        jobs.append(
                            Job(
                                external_id=job_id,
                                provider=self.name,
                                title=title,
                                company=company,
                                location=job_location,
                                url=href,
                                description=full_description,
                                remote=raw.get("workplace") == "remote",
                                country=country_name,
                                city=city,
                                posted_at=posted_at,
                            )
                        )

                        if len(jobs) >= limit:
                            break

                    next_token = data.get("nextPageToken")
                    if not next_token:
                        break

            logger.info(
                "workable_search_completed",
                extra={"query": query, "location": effective_location, "found": len(jobs)},
            )

            return jobs

        except Exception:
            logger.exception("workable_search_failed", extra={"query": query})
            return jobs
