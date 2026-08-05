import structlog
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from smarthunt.core.config import settings
from smarthunt.scheduler import scheduler
from smarthunt.scheduler.jobs import (
    check_email_replies,
    daily_morning_discovery,
    discover_devops,
    discover_linux,
    discover_openshift,
    discover_storage,
    discover_vmware,
    process_failed_scheduler_jobs,
    scan_all_linkedin_accounts_daily,
    scan_hashtags_daily,
    scan_linkedin_home_feed_hourly,
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
                discover_devops,
                IntervalTrigger(hours=5),
                id="discover_devops",
                replace_existing=True,
            )

            scheduler.add_job(
                process_failed_scheduler_jobs,
                IntervalTrigger(minutes=30),
                id="process_failed_scheduler_jobs",
                replace_existing=True,
            )

            scheduler.add_job(
                check_email_replies,
                IntervalTrigger(minutes=20),
                id="check_email_replies",
                replace_existing=True,
            )

            scheduler.add_job(
                scan_linkedin_home_feed_hourly,
                IntervalTrigger(hours=1),
                id="scan_linkedin_home_feed_hourly",
                replace_existing=True,
            )

            # hour=5 UTC = ~8am in Saudi Arabia (UTC+3) — the container's
            # own system timezone is UTC (see TZ=UTC in the configmap/
            # .env), and APScheduler's CronTrigger uses that by default,
            # so this has to be picked in UTC to actually land in the
            # morning locally rather than at literal "08:00 UTC" (11am
            # Saudi time).
            scheduler.add_job(
                daily_morning_discovery,
                CronTrigger(hour=5, minute=0),
                id="daily_morning_discovery",
                replace_existing=True,
            )

            scheduler.add_job(
                scan_all_linkedin_accounts_daily,
                CronTrigger(hour=5, minute=30),
                id="scan_all_linkedin_accounts_daily",
                replace_existing=True,
            )

            # hour=6 UTC (~9am Saudi) — after daily_morning_discovery
            # (5:00) and scan_all_linkedin_accounts_daily (5:30) so this
            # longer-running sweep (~31 hashtags, 30+ minutes) doesn't
            # pile CPU pressure on top of the other two daily jobs
            # starting at the same moment.
            scheduler.add_job(
                scan_hashtags_daily,
                CronTrigger(hour=6, minute=0),
                id="scan_hashtags_daily",
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
                    "discover_devops",
                    "process_failed_scheduler_jobs",
                    "check_email_replies",
                    "scan_linkedin_home_feed_hourly",
                    "daily_morning_discovery",
                    "scan_all_linkedin_accounts_daily",
                    "scan_hashtags_daily",
                ],
            )

        except Exception:
            logger.exception("scheduler_start_failed")
            raise
