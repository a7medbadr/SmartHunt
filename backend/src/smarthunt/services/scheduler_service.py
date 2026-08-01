import structlog
from apscheduler.triggers.interval import IntervalTrigger

from smarthunt.core.config import settings
from smarthunt.scheduler import scheduler
from smarthunt.scheduler.jobs import (
    discover_linux,
    discover_openshift,
    discover_storage,
    discover_vmware,
    process_failed_scheduler_jobs,
)

logger = structlog.get_logger()


class SchedulerService:

    def start(self) -> None:
        if not settings.scheduler_enabled:
            logger.info("scheduler_disabled")
            return

        if scheduler.running:
            logger.info("scheduler_already_running")
            return

        try:
            scheduler.add_job(
                discover_linux,
                IntervalTrigger(hours=1),
                id="discover_linux",
                replace_existing=True,
            )

            scheduler.add_job(
                discover_openshift,
                IntervalTrigger(hours=2),
                id="discover_openshift",
                replace_existing=True,
            )

            scheduler.add_job(
                discover_vmware,
                IntervalTrigger(hours=3),
                id="discover_vmware",
                replace_existing=True,
            )

            scheduler.add_job(
                discover_storage,
                IntervalTrigger(hours=4),
                id="discover_storage",
                replace_existing=True,
            )

            scheduler.add_job(
                process_failed_scheduler_jobs,
                IntervalTrigger(minutes=30),
                id="process_failed_scheduler_jobs",
                replace_existing=True,
            )

            scheduler.start()

            logger.info(
                "scheduler_started",
                jobs=[
                    "discover_linux",
                    "discover_openshift",
                    "discover_vmware",
                    "discover_storage",
                    "process_failed_scheduler_jobs",
                ],
            )

        except Exception:
            logger.exception("scheduler_start_failed")
            raise
