from typing import List
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.database.models.search_history import SearchHistory


class SearchHistoryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        query: str | None = None,
        provider: str | None = None,
        location: str | None = None,
        results_count: int = 0,
    ) -> SearchHistory:
        history = SearchHistory(
            query=query,
            provider=provider,
            location=location,
            results_count=results_count,
        )
        self.session.add(history)
        await self.session.commit()
        await self.session.refresh(history)
        return history

    async def list_recent(self, limit: int = 10) -> List[SearchHistory]:
        result = await self.session.execute(
            select(SearchHistory)
            .order_by(SearchHistory.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete_all(self) -> int:
        result = await self.session.execute(delete(SearchHistory))
        await self.session.commit()
        return result.rowcount
