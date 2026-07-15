import asyncio

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.browser.provider_executor import ProviderExecutor
from smarthunt.browser.registry import ProviderRegistry
from smarthunt.domain import DiscoveredJob
from smarthunt.services.job_service import JobService


class DiscoveryService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.jobs = JobService(db)
        self.registry = ProviderRegistry()

    async def discover(
        self,
        keyword: str,
        location: str | None = None,
    ):

        # إعداد الـ Executor والتنفيذ بالتوازي
        executor = ProviderExecutor(timeout=20)
        tasks = [
            executor.execute(provider, keyword, location)
            for provider in self.registry.get_all()
        ]
        results = await asyncio.gather(*tasks)

        # تجميع الوظائف من الـ نتائج الناجحة فقط
        all_jobs = []
        for result in results:
            if not result.success:
                continue
            all_jobs.extend(result.jobs)

        inserted = 0
        duplicates = 0
        saved: list[DiscoveredJob] = []

        # الفلترة والحفظ في قاعدة البيانات
        for job in all_jobs:
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
            "total_found": len(all_jobs),
            "inserted": inserted,
            "duplicates": duplicates,
            "jobs": saved,
        }
