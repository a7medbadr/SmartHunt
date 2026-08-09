from datetime import date, datetime, timedelta, timezone

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.dashboard.schemas import (
    DashboardStatisticsResponse,
    DashboardTimeseriesPoint,
    DashboardTimeseriesResponse,
)
from smarthunt.database.models.application import Application
from smarthunt.database.models.job import Job
from smarthunt.favorites.models import FavoriteJob
from smarthunt.providers.registry import provider_registry


class DashboardService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _count(self, model) -> int:
        result = await self.db.execute(select(func.count()).select_from(model))
        return result.scalar_one()

    async def get_statistics(self) -> DashboardStatisticsResponse:
        linkedin_posts_result = await self.db.execute(
            select(func.count()).select_from(Job).where(Job.source == "linkedin_post")
        )
        whatsapp_posts_result = await self.db.execute(
            select(func.count()).select_from(Job).where(Job.source == "whatsapp_message")
        )
        # NULL source counts as a "job site" job (e.g. manually created
        # via POST /jobs) — Job.source.notin_([...]) alone would silently
        # exclude those rows, since SQL's NOT IN against a NULL value is
        # NULL (falsy), not true.
        job_sites_result = await self.db.execute(
            select(func.count())
            .select_from(Job)
            .where(
                or_(
                    Job.source.is_(None),
                    Job.source.notin_(["linkedin_post", "whatsapp_message"]),
                )
            )
        )
        return DashboardStatisticsResponse(
            jobs=await self._count(Job),
            applications=await self._count(Application),
            favorites=await self._count(FavoriteJob),
            linkedin_posts=linkedin_posts_result.scalar_one(),
            whatsapp_posts=whatsapp_posts_result.scalar_one(),
            job_sites=job_sites_result.scalar_one(),
            providers=len(provider_registry.providers()),
        )

    async def get_timeseries(self, days: int = 14) -> DashboardTimeseriesResponse:
        today = datetime.now(timezone.utc).date()
        start_day = today - timedelta(days=days - 1)
        # Job.created_at is a naive UTC DateTime column, Application.created_at
        # is timezone-aware — each needs its own matching bound value, a naive
        # datetime compared against a tz-aware column (or vice versa) fails at
        # the asyncpg driver level rather than just giving a wrong answer.
        job_start = datetime.combine(start_day, datetime.min.time())
        app_start = datetime.combine(start_day, datetime.min.time(), tzinfo=timezone.utc)

        points_by_day: dict[date, DashboardTimeseriesPoint] = {
            start_day
            + timedelta(days=offset): DashboardTimeseriesPoint(
                date=start_day + timedelta(days=offset)
            )
            for offset in range(days)
        }

        job_bucket = case(
            (Job.source == "linkedin_post", "linkedin_posts"),
            (Job.source == "whatsapp_message", "whatsapp_posts"),
            else_="job_sites",
        ).label("bucket")
        job_day = func.date(Job.created_at).label("day")
        job_rows = await self.db.execute(
            select(job_day, job_bucket, func.count())
            .where(Job.created_at >= job_start)
            .group_by(job_day, job_bucket)
        )
        for day, bucket, count in job_rows.all():
            point = points_by_day.get(day)
            if point is not None:
                setattr(point, bucket, count)

        app_day = func.date(Application.created_at).label("day")
        app_rows = await self.db.execute(
            select(app_day, func.count())
            .where(Application.created_at >= app_start)
            .group_by(app_day)
        )
        for day, count in app_rows.all():
            point = points_by_day.get(day)
            if point is not None:
                point.applications = count

        return DashboardTimeseriesResponse(
            points=[points_by_day[day] for day in sorted(points_by_day)]
        )
