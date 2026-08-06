import asyncio
from datetime import datetime, timedelta, timezone

import structlog
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from smarthunt.core.config import settings
from smarthunt.scheduler import scheduler
from smarthunt.scheduler.jobs import (
    LINKEDIN_ACCOUNTS_PROVIDER,
    LINKEDIN_FEED_PROVIDER,
    LINKEDIN_HASHTAGS_PROVIDER,
    check_email_replies,
    daily_morning_discovery,
    discover_devops,
    discover_linux,
    discover_openshift,
    discover_storage,
    discover_vmware,
    linkedin_session_healthcheck,
    process_failed_scheduler_jobs,
    recycle_browser,
    scan_all_linkedin_accounts_daily,
    scan_hashtags_daily,
    scan_linkedin_home_feed_hourly,
)

logger = structlog.get_logger()


async def _run_catchup_jobs_sequentially(due_jobs: list) -> None:
    """Runs every overdue job one at a time, in a single background task
    — added 2026-08-06 after a real OpenShift OOM crash loop: the
    previous version fired each due job as its own separate
    `asyncio.create_task`, so on a restart where multiple jobs were
    overdue at once (routine — e.g. discover_linux and discover_vmware
    both overdue after any downtime past an hour), several full discovery
    passes (each fanning out across ~11 providers, several driving real
    Chromium) ran fully concurrently within seconds of startup. Confirmed
    live via `oc describe pod`/`--previous` logs: the pod was OOMKilled
    (2Gi limit) twice in immediate succession, each time within ~2
    minutes of `scheduler_started`, right after `scheduler:linux` and
    `scheduler:vmware` catchup both fired in the same few milliseconds —
    a crash loop, since every restart re-triggered the same overdue jobs
    again. Running them sequentially instead keeps at most one heavy
    catch-up job's memory footprint active at a time, while still not
    blocking the startup/readiness probes (this whole function is itself
    one background task, same as before — only what happens *inside* it
    changed from concurrent to sequential)."""
    for job_func in due_jobs:
        try:
            await job_func()
        except Exception:
            logger.exception("scheduled_job_catchup_run_failed", job=job_func.__name__)


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

            # Every 30 min — see linkedin_session_healthcheck's own
            # docstring for why not the literally-requested 5-10 (abuse-
            # detection risk from re-submitting credentials too often).
            scheduler.add_job(
                linkedin_session_healthcheck,
                IntervalTrigger(minutes=30),
                id="linkedin_session_healthcheck",
                replace_existing=True,
            )

            # Every 6h — bounds how long Chromium's own idle renderer-
            # process pool can accumulate on this resource-constrained
            # shared host (see recycle_browser's docstring for the live
            # incident that motivated this: a stale renderer process
            # pinned at 66% CPU for 87+ minutes with no active scan
            # running was enough to push a trivial Ollama request past a
            # 90s timeout). A recycle landing mid-scan can make that one
            # provider's run return fewer/zero results for that cycle
            # (its context.close()/goto() just raises into the same
            # broad try/except every provider already has) — an accepted,
            # self-healing tradeoff against letting the host degrade
            # unbounded over many hours of uptime.
            scheduler.add_job(
                recycle_browser,
                IntervalTrigger(hours=6),
                id="recycle_browser",
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
                    "linkedin_session_healthcheck",
                    "recycle_browser",
                    "daily_morning_discovery",
                    "scan_all_linkedin_accounts_daily",
                    "scan_hashtags_daily",
                ],
            )

        except Exception:
            logger.exception("scheduler_start_failed")
            raise

    async def catch_up_scheduled_jobs(self) -> None:
        """Startup catch-up for every interval/cron scheduled job that
        writes to scheduler_history — added 2026-08-05, originally just for
        the three LinkedIn-monitor jobs after finding scan_hashtags_daily
        (CronTrigger hour=6) had never once fired in over two days of real
        container logs, then widened the same day to also cover the five
        core discover_* jobs after the owner reported "my home page search
        doesn't seem to run every hour" and scheduler_history confirmed a
        real ~17h gap in discover_linux/openshift/vmware/storage/devops —
        the exact same shape of bug, just on the app's most central
        automated feature. Root cause for all eight: this host's backend
        restarts far more often than these jobs' own intervals (routine
        rebuilds/redeploys, plus at least one unplanned multi-hour downtime
        window found live), and APScheduler's IntervalTrigger/CronTrigger
        only schedule their *first* run at start-time-plus-interval, never
        immediately — so a fixed trigger can silently miss its window
        entirely, sometimes for many hours or days running, with nothing to
        catch it back up on its own. Checks scheduler_history for each
        job's last real run and fires it once in the background if it
        hasn't run recently enough. Self-limiting by design — a job that
        already ran within its own window this restart is a no-op — so this
        is safe to call unconditionally on every startup, however frequent."""
        if not settings.scheduler_enabled:
            return

        from smarthunt.database.session import AsyncSessionLocal
        from smarthunt.scheduler.history.service import scheduler_history_service

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Same max-age as each job's own recurring trigger (see start()
        # above) — a run that already happened within that window this
        # restart doesn't need catching up, it's simply not due yet.
        checks = [
            ("scheduler:linux", timedelta(hours=1), discover_linux),
            ("scheduler:openshift", timedelta(hours=2), discover_openshift),
            ("scheduler:vmware", timedelta(hours=3), discover_vmware),
            ("scheduler:storage", timedelta(hours=4), discover_storage),
            ("scheduler:devops", timedelta(hours=5), discover_devops),
            (LINKEDIN_FEED_PROVIDER, timedelta(hours=1), scan_linkedin_home_feed_hourly),
            (LINKEDIN_ACCOUNTS_PROVIDER, timedelta(days=1), scan_all_linkedin_accounts_daily),
            (LINKEDIN_HASHTAGS_PROVIDER, timedelta(days=1), scan_hashtags_daily),
        ]

        due_jobs = []

        async with AsyncSessionLocal() as db:
            for provider, max_age, job_func in checks:
                try:
                    latest = await scheduler_history_service.latest_for_provider(db, provider)
                except Exception:
                    logger.exception("scheduled_job_catchup_check_failed", provider=provider)
                    continue

                due = latest is None or (now - latest.started_at) > max_age
                if not due:
                    continue

                logger.info(
                    "scheduled_job_catchup_triggered",
                    provider=provider,
                    last_run=latest.started_at.isoformat() if latest else None,
                )
                due_jobs.append(job_func)

        if due_jobs:
            asyncio.create_task(_run_catchup_jobs_sequentially(due_jobs))
