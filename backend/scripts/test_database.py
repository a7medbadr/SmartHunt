import asyncio

from smarthunt.database.models.job import Job
from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.database.session import AsyncSessionLocal


async def main():
    async with AsyncSessionLocal() as session:
        repository = JobRepository(session)

        job = Job(
            title="Linux Engineer",
            company="Red Hat",
            location="Riyadh",
            source="Manual",
            url="https://example.com/job/1",
        )

        await repository.create(job)

        jobs = await repository.get_all()

        print(f"Jobs in database: {len(jobs)}")

        first = await repository.get(job.id)

        print(first.title)


asyncio.run(main())
