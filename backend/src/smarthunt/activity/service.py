from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from smarthunt.activity.models import Activity
from smarthunt.activity.schemas import ActivityCreate

class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_activity(self, data: ActivityCreate) -> Activity:
        activity = Activity(
            type=data.type,
            title=data.title,
            details=data.details
        )
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def get_recent_activities(self, limit: int = 20) -> List[Activity]:
        query = (
            select(Activity)
            .order_by(Activity.created_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())
