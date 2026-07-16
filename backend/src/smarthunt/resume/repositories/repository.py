from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        user_id: int,
        filename: str,
        stored_path: str,
        extracted_text: str,
    ) -> Resume:

        resume = Resume(
            user_id=user_id,
            filename=filename,
            stored_path=stored_path,
            extracted_text=extracted_text,
        )

        self.db.add(resume)

        await self.db.commit()

        await self.db.refresh(resume)

        return resume
