import logging
from typing import Dict, Any, List
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.search.schemas import SearchJobQueryParams
from smarthunt.database.repositories.job_repository import JobRepository
from smarthunt.database.models.search_history import SearchHistoryModel

logger = logging.getLogger("smarthunt.search")


class SearchService:
    @staticmethod
    async def execute_search(db: AsyncSession, params: SearchJobQueryParams) -> Dict[str, Any]:
        repo = JobRepository(db)
        jobs, total = await repo.search_jobs(params)

        # Convert ORM to JSON-friendly response
        formatted_jobs = [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "provider": job.provider,
                "location": job.location,
                "salary": job.salary,
                "score": job.score,
                "created_at": job.created_at.isoformat() if job.created_at else None
            }
            for job in jobs
        ]

        # Log Search History (Sprint 81)
        history_entry = SearchHistoryModel(
            query=params.title,
            provider=params.provider,
            location=params.location,
            results_count=total
        )
        db.add(history_entry)
        await db.commit()

        return {
            "jobs": formatted_jobs,
            "total": total,
            "page": params.page,
            "limit": params.limit
        }

    @staticmethod
    async def get_search_history(db: AsyncSession, limit: int = 100) -> List[Dict[str, Any]]:
        stmt = select(SearchHistoryModel).order_by(desc(SearchHistoryModel.created_at)).limit(limit)
        result = await db.execute(stmt)
        history_records = result.scalars().all()

        return [
            {
                "id": h.id,
                "query": h.query,
                "provider": h.provider,
                "location": h.location,
                "results_count": h.results_count,
                "created_at": h.created_at.isoformat() if h.created_at else None
            }
            for h in history_records
        ]

# Instance export for router dependency
search_service = SearchService()
