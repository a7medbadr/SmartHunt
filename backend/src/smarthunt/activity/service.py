from typing import List, Optional

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from smarthunt.activity.models import Activity, ActivityType
from smarthunt.activity.schemas import ActivityCreate

logger = structlog.get_logger("smarthunt")


class ActivityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_activity(self, data: ActivityCreate) -> Activity:
        activity = Activity(type=data.type, title=data.title, details=data.details)
        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)
        return activity

    async def get_recent_activities(self, limit: int = 20) -> List[Activity]:
        query = select(Activity).order_by(Activity.created_at.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())


async def log_activity(
    db: AsyncSession,
    activity_type: ActivityType,
    title: str,
    details: Optional[str] = None,
) -> None:
    """Best-effort activity log — never let a logging failure break the
    real operation it's attached to."""
    try:
        await ActivityService(db).create_activity(
            ActivityCreate(type=activity_type, title=title, details=details)
        )
    except Exception:
        logger.exception("activity_log_failed", activity_type=activity_type.value)
