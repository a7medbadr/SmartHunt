from typing import List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.job_tags.models import JobTag
from smarthunt.job_tags.schemas import JobTagCreate


class JobTagAlreadyExistsError(Exception):
    pass


class JobTagNotFoundError(Exception):
    pass


class JobTagService:
    async def add_tag(self, db: AsyncSession, data: JobTagCreate) -> JobTag:
        result = await db.execute(
            select(JobTag).where(
                JobTag.job_id == data.job_id,
                func.lower(JobTag.tag) == data.tag.strip().lower(),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise JobTagAlreadyExistsError(f"Tag '{data.tag}' already exists for job {data.job_id}")

        tag = JobTag(job_id=data.job_id, tag=data.tag.strip())
        db.add(tag)
        await db.flush()
        await db.refresh(tag)
        return tag

    async def list_tags_by_job(self, db: AsyncSession, job_id: int) -> List[JobTag]:
        result = await db.execute(
            select(JobTag).where(JobTag.job_id == job_id).order_by(JobTag.created_at)
        )
        return list(result.scalars().all())

    async def get_tag(self, db: AsyncSession, tag_id: int) -> JobTag:
        result = await db.execute(select(JobTag).where(JobTag.id == tag_id))
        tag = result.scalar_one_or_none()
        if tag is None:
            raise JobTagNotFoundError(f"Job tag with id {tag_id} not found")
        return tag

    async def delete_tag(self, db: AsyncSession, tag_id: int) -> None:
        tag = await self.get_tag(db, tag_id)
        await db.delete(tag)
        await db.flush()


job_tag_service = JobTagService()
