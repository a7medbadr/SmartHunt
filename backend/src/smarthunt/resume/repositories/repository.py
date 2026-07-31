from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.resume import Resume


class ResumeRepository:

    def __init__(
        self,
        db: AsyncSession,
    ):
        self.db = db

    async def create(
        self,
        *,
        user_id: int,
        filename: str,
        stored_path: str,
        extracted_text: str | None = None,
    ) -> Resume:

        resume = Resume(
            user_id=user_id,
            filename=filename,
            stored_path=stored_path,
            extracted_text=extracted_text,
        )

        self.db.add(resume)

        await self.db.flush()

        await self.db.refresh(resume)

        return resume

    async def get_by_id(
        self,
        resume_id: int,
    ) -> Resume | None:

        result = await self.db.execute(select(Resume).where(Resume.id == resume_id))

        return result.scalar_one_or_none()

    async def get_by_user(
        self,
        user_id: int,
    ) -> list[Resume]:

        result = await self.db.execute(select(Resume).where(Resume.user_id == user_id))

        return list(result.scalars().all())

    async def delete(
        self,
        resume: Resume,
    ) -> None:

        await self.db.delete(resume)

        await self.db.flush()
