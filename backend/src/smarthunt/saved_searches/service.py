from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.saved_searches.models import SavedSearch
from smarthunt.saved_searches.schemas import SavedSearchCreate


class SavedSearchNotFoundError(Exception):
    pass


class SavedSearchService:
    async def create(self, db: AsyncSession, data: SavedSearchCreate) -> SavedSearch:
        search = SavedSearch(
            name=data.name,
            keyword=data.keyword,
            location=data.location,
        )
        db.add(search)
        await db.flush()
        await db.refresh(search)
        return search

    async def list_all(self, db: AsyncSession) -> List[SavedSearch]:
        result = await db.execute(select(SavedSearch).order_by(SavedSearch.created_at))
        return list(result.scalars().all())

    async def get(self, db: AsyncSession, search_id: int) -> SavedSearch:
        result = await db.execute(select(SavedSearch).where(SavedSearch.id == search_id))
        search = result.scalar_one_or_none()
        if search is None:
            raise SavedSearchNotFoundError(f"Saved search with id {search_id} not found")
        return search

    async def delete(self, db: AsyncSession, search_id: int) -> None:
        search = await self.get(db, search_id)
        await db.delete(search)
        await db.flush()


saved_search_service = SavedSearchService()
