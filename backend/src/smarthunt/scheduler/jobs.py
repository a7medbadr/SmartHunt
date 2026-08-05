import logging

from smarthunt.database.session import AsyncSessionLocal
from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job_service import failed_scheduler_job_service
from smarthunt.scheduler.retry_worker import TOPIC_QUERIES, scheduler_retry_worker

logger = logging.getLogger("smarthunt.scheduler")

# Saudi Arabia only, per the project owner's explicit requirement — see
# CLAUDE.md's "Discovery scope" note before broadening this.
DISCOVERY_LOCATION = "Saudi Arabia"

# The owner's own hashtag list (2026-08-05), deduplicated — a mix of
# general hiring/location tags and their specific tech stack. Scanned
# daily (see scan_hashtags_daily below), not hourly: at ~60-65s/hashtag
# measured live, ~31 hashtags is already a 30+ minute run, and this
# machine only has 3 CPU cores shared with everything else (Postgres,
# Ollama, the backend itself) — hourly would leave almost no idle time
# for anything else to actually get CPU.
HASHTAG_LIST = [
    "Hiring",
    "HiringNow",
    "HiringAlert",
    "SaudiJobs",
    "SaudiArabia",
    "SaudiArabiaJobs",
    "KSAJobs",
    "RiyadhJobs",
    "ITJobs",
    "TechJobs",
    "Infrastructure",
    "InfrastructureLead",
    "ITSupport",
    "FieldSupport",
    "DesktopSupport",
    "SystemAdministration",
    "Cloud",
    "CloudInfrastructure",
    "Networking",
    "OnsiteJobs",
    "Recruitment",
    "CareerOpportunities",
    "JoinUs",
    "Linux",
    "RHEL",
    "RHCE",
    "Ansible",
    "Terraform",
    "Kubernetes",
    "CKA",
    "DevOps",
    "Automation",
]


async def _run_scheduled_discovery(topic: str, query: str) -> None:
    """Run a real discovery pass for `query` across every provider and
    persist results, tracking success/failure via the same
    scheduler_history / failed_scheduler_job tables the Scheduler page
    reads from."""
    provider_label = f"scheduler:{topic}"

    async with AsyncSessionLocal() as db:
        try:
            result = await DiscoveryService(db).discover(
                query=query,
                location=DISCOVERY_LOCATION,
                provider=provider_label,
            )
            await db.commit()
            logger.info(
                "scheduled_discovery_completed",
                extra={"topic": topic, **result},
            )
        except Exception as exc:
            logger.exception("scheduled_discovery_failed", extra={"topic": topic})
            await db.rollback()
            await failed_scheduler_job_service.create(
                db,
                provider=provider_label,
                job_reference=topic,
                error=str(exc),
            )
            await db.commit()
            raise


async def discover_linux():
    await _run_scheduled_discovery("linux", TOPIC_QUERIES["linux"])


async def discover_openshift():
    await _run_scheduled_discovery("openshift", TOPIC_QUERIES["openshift"])


async def discover_vmware():
    await _run_scheduled_discovery("vmware", TOPIC_QUERIES["vmware"])


async def discover_storage():
    await _run_scheduled_discovery("storage", TOPIC_QUERIES["storage"])


async def discover_devops():
    await _run_scheduled_discovery("devops", TOPIC_QUERIES["devops"])


async def process_failed_scheduler_jobs():
    """Periodic sweep that retries FAILED scheduler jobs (with backoff via
    retry_count) instead of letting them accumulate forever unprocessed."""
    async with AsyncSessionLocal() as db:
        processed = await scheduler_retry_worker.process(db)
        await db.commit()
        logger.info(
            "scheduler_retry_sweep_completed",
            extra={"processed": len(processed)},
        )


async def check_email_replies():
    """Periodic IMAP poll for replies to sent application emails — see
    email_apply/service.py::check_for_replies. Notifies the owner
    immediately when a real reply lands so they can decide whether/how
    to respond, rather than the owner having to remember to check."""
    from smarthunt.email_apply.service import check_for_replies

    async with AsyncSessionLocal() as db:
        found = await check_for_replies(db)
        await db.commit()
        logger.info(
            "email_reply_check_completed",
            extra={"new_replies": len(found)},
        )


async def scan_linkedin_home_feed_hourly():
    """Every hour, scans the owner's own LinkedIn home feed (first ~50
    posts) for job-relevant posts and saves any real match — the
    automatic counterpart to the "افحص الصفحة الرئيسية بتاعتي" manual
    button on the job-search page, added 2026-08-04 per explicit
    request so this doesn't require remembering to click it."""
    from smarthunt.linkedin_monitor import service as linkedin_monitor_service
    from smarthunt.linkedin_monitor.post_scanner import scan_home_feed

    async with AsyncSessionLocal() as db:
        try:
            posts = await scan_home_feed()
            saved = await linkedin_monitor_service.scan_and_save(db, posts)
            logger.info(
                "scheduled_linkedin_feed_scan_completed",
                extra={"scanned": len(posts), "saved": len(saved)},
            )
        except Exception:
            logger.exception("scheduled_linkedin_feed_scan_failed")


async def daily_morning_discovery():
    """Once a day (see scheduler_service.py for the actual time), runs a
    full discovery sweep across every tracked topic — a guaranteed daily
    pass on top of the existing hourly/interval jobs above, added
    2026-08-04 per explicit request ("كل يوم الصبح ... يروح يبحث في
    الوظائف بتاعتها")."""
    for topic, query in TOPIC_QUERIES.items():
        try:
            await _run_scheduled_discovery(f"daily-morning-{topic}", query)
        except Exception:
            # _run_scheduled_discovery already logs/records the failure —
            # one topic failing shouldn't skip the rest of the sweep.
            continue


async def scan_all_linkedin_accounts_daily():
    """Once a day, scans every enabled monitored LinkedIn account's own
    recent posts (same extraction as the manual "افحص دلوقتي" button)
    for job-relevant content — added 2026-08-04 per explicit request so
    a newly-added HR/person account gets checked automatically going
    forward, not just once at add-time. Not a literal "last 24h" time
    filter (LinkedIn's post markup doesn't expose a cleanly parseable
    timestamp — see linkedin_monitor/post_scanner.py) — in practice, a
    daily scan of each account's most recent posts plus save_post_as_job's
    dedup-by-post_url achieves the same "don't miss anything new since
    yesterday" outcome."""
    from smarthunt.linkedin_monitor import service as linkedin_monitor_service
    from smarthunt.linkedin_monitor.post_scanner import scan_profile_posts

    async with AsyncSessionLocal() as db:
        accounts = await linkedin_monitor_service.list_accounts(db)

    for account in accounts:
        if not account.enabled:
            continue

        async with AsyncSessionLocal() as db:
            try:
                posts = await scan_profile_posts(account.profile_url)
                saved = await linkedin_monitor_service.scan_and_save(db, posts)
                await linkedin_monitor_service.mark_account_checked(db, account.id)
                logger.info(
                    "scheduled_linkedin_account_scan_completed",
                    extra={
                        "account_id": account.id,
                        "scanned": len(posts),
                        "saved": len(saved),
                    },
                )
            except Exception:
                logger.exception(
                    "scheduled_linkedin_account_scan_failed",
                    extra={"account_id": account.id},
                )
                continue


async def scan_hashtags_daily():
    """Once a day, scans the first ~50 posts under every hashtag in
    HASHTAG_LIST for job-relevant content — the automatic counterpart to
    the manual "افحص الهاشتاجات" block on the job-search page, added
    2026-08-05 per explicit request. One hashtag failing (navigation
    error, etc.) doesn't skip the rest of the list."""
    from smarthunt.linkedin_monitor import service as linkedin_monitor_service
    from smarthunt.linkedin_monitor.post_scanner import scan_hashtag_posts

    for hashtag in HASHTAG_LIST:
        async with AsyncSessionLocal() as db:
            try:
                posts = await scan_hashtag_posts(hashtag)
                saved = await linkedin_monitor_service.scan_and_save(db, posts)
                logger.info(
                    "scheduled_hashtag_scan_completed",
                    extra={"hashtag": hashtag, "scanned": len(posts), "saved": len(saved)},
                )
            except Exception:
                logger.exception("scheduled_hashtag_scan_failed", extra={"hashtag": hashtag})
                continue
                continue
