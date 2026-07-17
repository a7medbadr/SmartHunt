from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.job import Job


class JobRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def exists(self, provider: str, title: str, location: str) -> bool:
        result = await self.session.execute(
            select(Job).where(
                Job.provider == provider,
                Job.title == title,
                Job.location == location,
            )
        )
        return result.scalar_one_or_none() is not None

    async def save_many(self, jobs: list[dict]) -> int:
        inserted = 0

        for item in jobs:

            if await self.exists(
                item["provider"],
                item["title"],
                item["location"],
            ):
                continue

            self.session.add(Job(**item))
            inserted += 1

        await self.session.commit()

        return inserted

    async def list_all(self):

        result = await self.session.execute(
            select(Job).order_by(Job.score.desc())
        )

        return result.scalars().all()
