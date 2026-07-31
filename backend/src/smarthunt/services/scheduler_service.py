import structlog
from apscheduler.triggers.interval import IntervalTrigger

from smarthunt.core.config import settings
from smarthunt.scheduler import scheduler
from smarthunt.scheduler.jobs import (
    discover_devops,
    discover_linux,
    discover_python,
)

logger = structlog.get_logger()


class SchedulerService:

    def start(self) -> None:
        if not settings.scheduler_enabled:
            logger.info(
                "scheduler_disabled"
            )
            return

        if scheduler.running:
            logger.info(
                "scheduler_already_running"
            )
            return

        try:
            scheduler.add_job(
                discover_python,
                IntervalTrigger(hours=1),
                id="discover_python",
                replace_existing=True,
            )

            scheduler.add_job(
                discover_linux,
                IntervalTrigger(hours=2),
                id="discover_linux",
                replace_existing=True,
            )

            scheduler.add_job(
                discover_devops,
                IntervalTrigger(hours=3),
                id="discover_devops",
                replace_existing=True,
            )

            scheduler.start()

            logger.info(
                "scheduler_started",
                jobs=[
                    "discover_python",
                    "discover_linux",
                    "discover_devops",
                ],
            )

        except Exception:
            logger.exception(
                "scheduler_start_failed"
            )
            raise
