from __future__ import annotations

import re

from sqlalchemy import asc
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job
from smarthunt.domain.job import DiscoveredJob

# Cross-source duplicate detection — found 2026-08-13 that the same real
# opening routinely gets discovered twice under different `source`s (e.g.
# a DeepSource Technologies role picked up by both Tanqeeb and Workable,
# confirmed live via direct DB inspection), because the old exists() check
# scoped its match to `source == source`, so two different providers
# reporting the same job never got compared against each other at all.
# Normalizes away case/punctuation/whitespace noise (provider-specific
# formatting like "Riyadh, KSA" suffixes on the title, "Openshift" vs
# "OpenShift" casing) rather than requiring byte-identical strings.
_NORMALIZE_PATTERN = re.compile(r"[^a-z0-9؀-ۿ]+")

# Corporate-entity suffix words to strip before comparing two company
# names — a plain substring check (does "DeepSource" appear inside
# "DeepSource Technologies") was tried first and reverted: it also
# matched unrelated companies that just happen to share a leading word
# ("Acme Riyadh" contains "Acme", which any other unrelated "Acme ..."
# company would too — a real regression caught by
# test_discover_lets_remote_jobs_through_a_physical_location_filter's
# three deliberately-distinct "Acme"-prefixed companies). Stripping known
# suffixes and requiring the remainder to match exactly is narrower but
# correct for the actual observed case (DeepSource / DeepSource
# Technologies, confirmed live via direct DB inspection).
_COMPANY_SUFFIX_WORDS = frozenset(
    {
        "technologies",
        "technology",
        "tech",
        "solutions",
        "solution",
        "group",
        "trading",
        "co",
        "company",
        "inc",
        "llc",
        "ltd",
        "corporation",
        "corp",
        "est",
        "establishment",
    }
)


def _normalize(value: str | None) -> str:
    if not value:
        return ""
    return _NORMALIZE_PATTERN.sub(" ", value.lower()).strip()


def _company_key(value: str | None) -> str:
    words = _normalize(value).split()
    while words and words[-1] in _COMPANY_SUFFIX_WORDS:
        words.pop()
    return " ".join(words)


class JobRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, job: Job) -> Job:
        self.session.add(job)
        await self.session.commit()
        await self.session.refresh(job)
        return job

    async def get(self, job_id: int):
        result = await self.session.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def get_all(self):
        result = await self.session.execute(select(Job))
        return list(result.scalars())

    async def delete(self, job_id: int):

        job = await self.get(job_id)

        if job is None:
            return False

        await self.session.delete(job)
        await self.session.commit()

        return True

    async def exists(
        self,
        source: str,
        title: str,
        location: str | None,
    ) -> bool:

        stmt = (
            select(Job.id)
            .where(Job.source == source)
            .where(Job.title == title)
            .where(Job.location == location)
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def _load_dedup_index(self) -> list[tuple[str, str, str | None, str | None]]:
        """One query for (normalized title, normalized company, url,
        post_url) across every existing job, of every source — the shared
        index save_discovered_jobs()/is_duplicate() match new jobs against,
        so a duplicate is caught no matter which provider originally
        inserted the existing row."""
        stmt = select(Job.title, Job.company, Job.url, Job.post_url)
        rows = (await self.session.execute(stmt)).all()
        return [(_normalize(t), _company_key(c), u, p) for t, c, u, p in rows]

    @staticmethod
    def _matches_index(
        index: list[tuple[str, str, str | None, str | None]],
        title: str,
        company: str | None,
        url: str | None = None,
    ) -> bool:
        norm_title = _normalize(title)
        company_key = _company_key(company)
        for sig_title, sig_company_key, sig_url, sig_post_url in index:
            if url and (url == sig_url or url == sig_post_url):
                return True
            if (
                norm_title
                and norm_title == sig_title
                and company_key
                and company_key == sig_company_key
            ):
                return True
        return False

    async def is_duplicate(self, title: str, company: str | None, url: str | None = None) -> bool:
        """Cross-source duplicate check for a single job — used by
        linkedin_monitor/whatsapp_monitor's save paths, which each insert
        one item at a time rather than a batch."""
        index = await self._load_dedup_index()
        return self._matches_index(index, title, company, url)

    async def save_discovered_jobs(
        self,
        jobs: list[DiscoveredJob],
    ) -> int:

        index = await self._load_dedup_index()
        inserted = 0

        for item in jobs:

            if self._matches_index(index, item.title, item.company, item.url):
                continue

            self.session.add(
                Job(
                    title=item.title,
                    company=item.company,
                    location=item.location,
                    description=item.description,
                    requirements=item.requirements,
                    source=item.source,
                    url=item.url,
                    posted_at=item.posted_at,
                )
            )

            # Track this batch's own newly-added jobs too, so two
            # providers returning the same job in the same discover() call
            # don't both get inserted just because neither is in the DB yet.
            index.append((_normalize(item.title), _company_key(item.company), item.url, None))

            inserted += 1

        await self.session.commit()

        return inserted

    async def search_jobs(self, params):

        stmt = select(Job)

        if getattr(params, "title", None):
            stmt = stmt.where(Job.title.ilike(f"%{params.title}%"))

        if getattr(params, "company", None):
            stmt = stmt.where(Job.company.ilike(f"%{params.company}%"))

        if getattr(params, "location", None):
            stmt = stmt.where(Job.location.ilike(f"%{params.location}%"))

        if getattr(params, "provider", None):
            stmt = stmt.where(Job.source.ilike(f"%{params.provider}%"))

        total = (
            await self.session.execute(select(func.count()).select_from(stmt.subquery()))
        ).scalar_one()

        sort_name = getattr(
            params,
            "sort",
            "created_at",
        )

        sort_attr = getattr(
            Job,
            sort_name,
            Job.created_at,
        )

        if (
            str(
                getattr(
                    params,
                    "order",
                    "desc",
                )
            ).lower()
            == "asc"
        ):
            stmt = stmt.order_by(asc(sort_attr))
        else:
            stmt = stmt.order_by(desc(sort_attr))

        page = getattr(params, "page", 1)
        limit = getattr(params, "limit", 10)

        stmt = stmt.offset((page - 1) * limit).limit(limit)

        result = await self.session.execute(stmt)

        return list(result.scalars()), total
