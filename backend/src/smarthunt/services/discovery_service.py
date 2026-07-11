from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.domain import DiscoveredJob
from smarthunt.services.job_service import JobService
from smarthunt.services.scraper_service import ScraperService


class DiscoveryService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.jobs = JobService(db)
        self.scraper = ScraperService()

    async def discover(
        self,
        keyword: str,
        location: str | None = None,
    ):

        discovered = await self.scraper.search(
            keyword=keyword,
            location=location,
        )

        inserted = 0
        duplicates = 0

        saved: list[DiscoveredJob] = []

        for job in discovered:

            try:
                db_job = await self.jobs.create_job(
                    title=job.title.strip() if job.title else "",
                    company=job.company.strip() if job.company else "",
                    location=job.location.strip() if job.location else "",
                    source=job.source,
                    url=str(job.url) if job.url else "",
                )

                inserted += 1

                saved.append(
                    DiscoveredJob(
                        title=db_job.title,
                        company=db_job.company,
                        location=db_job.location,
                        source=db_job.source,
                        url=db_job.url,
                    )
                )

            except IntegrityError:
                await self.db.rollback()
                duplicates += 1

        return {
            "total_found": len(discovered),
            "inserted": inserted,
            "duplicates": duplicates,
            "jobs": saved,
        }
