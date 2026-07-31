from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.favorites.models import FavoriteJob
from smarthunt.favorites.schemas import FavoriteJobCreate


class FavoriteAlreadyExistsError(Exception):
    pass


class FavoriteNotFoundError(Exception):
    pass


class FavoritesService:
    async def add_favorite(self, db: AsyncSession, data: FavoriteJobCreate) -> FavoriteJob:
        result = await db.execute(select(FavoriteJob).where(FavoriteJob.job_id == data.job_id))
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise FavoriteAlreadyExistsError(f"Job with id {data.job_id} is already in favorites")

        favorite = FavoriteJob(job_id=data.job_id)
        db.add(favorite)
        await db.flush()
        await db.refresh(favorite)
        return favorite

    async def list_favorites(self, db: AsyncSession) -> List[FavoriteJob]:
        result = await db.execute(select(FavoriteJob).order_by(FavoriteJob.created_at))
        return list(result.scalars().all())

    async def delete_favorite(self, db: AsyncSession, job_id: int) -> None:
        result = await db.execute(select(FavoriteJob).where(FavoriteJob.job_id == job_id))
        favorite = result.scalar_one_or_none()
        if favorite is None:
            raise FavoriteNotFoundError(f"Favorite with job_id {job_id} not found")
        await db.delete(favorite)
        await db.flush()


favorites_service = FavoritesService()
