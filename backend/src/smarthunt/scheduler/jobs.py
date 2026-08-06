import logging

from smarthunt.database.session import AsyncSessionLocal
from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job_service import failed_scheduler_job_service
from smarthunt.scheduler.retry_worker import TOPIC_QUERIES, scheduler_retry_worker

logger = logging.getLogger("smarthunt.scheduler")

# Saudi Arabia only, per the project owner's explicit requirement — see
# CLAUDE.md's "Discovery scope" note before broadening this.
DISCOVERY_LOCATION = "Saudi Arabia"

# scheduler_history provider labels for the three LinkedIn-monitor jobs
# below — added 2026-08-05 alongside SchedulerService's startup catch-up
# check (services/scheduler_service.py), which reads these same labels
# back out of scheduler_history to decide whether today's/this hour's run
# already happened. Before this, these three jobs only ever logged via
# structlog (no scheduler_history row at all), so the job-search page's
# run history couldn't show them, and there was no way to tell "did this
# actually run today" without grepping container logs.
LINKEDIN_FEED_PROVIDER = "scheduler:linkedin-feed"
LINKEDIN_ACCOUNTS_PROVIDER = "scheduler:linkedin-accounts"
LINKEDIN_HASHTAGS_PROVIDER = "scheduler:linkedin-hashtags"

# The owner's original hashtag list (2026-08-05) — moved 2026-08-06 into
# the DB-backed MonitoredHashtag table (linkedin_monitor/models.py) so
# each hashtag is individually addable/removable/enabled from the
# job-search page, the same as monitored accounts. The seed migration
# (alembic/versions/) populates this same list into that table on
# upgrade; scan_hashtags_daily below now reads from the DB, filtered to
# enabled=True, instead of this constant. At ~60-65s/hashtag measured
# live, the full ~31-hashtag list is already a 30+ minute run, and this
# machine only has 3 CPU cores shared with everything else (Postgres,
# Ollama, the backend itself) — hourly would leave almost no idle time
# for anything else to actually get CPU, hence still daily, not hourly.


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


async def linkedin_session_healthcheck():
    """Periodically verifies the persistent LinkedIn session is still
    logged in, and attempts a real re-login if not — added 2026-08-06 per
    explicit request ("عاوز سكربت يفضل فاتح سيشن مفتوحه بين المشروع
    ولينكدان") so the hourly/daily LinkedIn scans always have a live
    session instead of silently degrading as cookies age out over days.

    Deliberately every 30 minutes, not the literally-requested 5-10:
    `linkedin_login()` re-submitting credentials too often is exactly
    what already triggered LinkedIn's own repeated-login abuse detection
    once before on this project (see browser/playwright/manager.py's
    BROWSER_PROFILES_DIR note) — 30 minutes is frequent enough to catch a
    dropped session same-day without hammering LinkedIn's login endpoint.
    Also, when the session really is logged out, a *full* automated
    recovery isn't safely unattended at all: LinkedIn's own device-
    approval checkpoint needs the owner to tap a push notification on
    their phone (see CLAUDE.md's LinkedIn login notes) — this job
    attempts one real `linkedin_login()` call (cheap when already logged
    in — see that function's own early-return for an already-authenticated
    session), and if that comes back MANUAL_REQUIRED, notifies the owner
    instead of retrying blindly, matching the project's standing "only
    CAPTCHA/MFA should ever pause and wait for a human" rule rather than
    silently looping forever on something a script cannot solve.

    Shares post_scanner.py's `_linkedin_page_lock` since this navigates
    the same persistent "linkedin" page every other LinkedIn scan
    function does — skips this run entirely (rather than blocking) if a
    scan is already using it, same bounded-wait pattern as those
    functions use for the reverse case."""
    from smarthunt.browser.playwright.manager import browser_manager
    from smarthunt.browser.providers.linkedin.login import linkedin_login
    from smarthunt.linkedin_monitor.post_scanner import (
        _linkedin_page_lock,
        _try_acquire_linkedin_lock,
    )
    from smarthunt.notifications.schemas import NotificationCreate
    from smarthunt.notifications.service import notification_service

    try:
        if not browser_manager.is_running:
            await browser_manager.launch()

        if not await _try_acquire_linkedin_lock():
            logger.info("linkedin_session_healthcheck_skipped_busy")
            return

        try:
            page = await browser_manager.get_page("linkedin")
            result = await linkedin_login(page)
        finally:
            _linkedin_page_lock.release()

        status = result.get("status")

        if status == "SUCCESS":
            await browser_manager.save_state("linkedin")
            logger.info("linkedin_session_healthcheck_ok")
            return

        logger.warning("linkedin_session_healthcheck_failed", extra={"status": status})

        if status == "MANUAL_REQUIRED":
            async with AsyncSessionLocal() as db:
                await notification_service.create(
                    db,
                    NotificationCreate(
                        type="WARNING",
                        title="لينكدان محتاج تدخل يدوي",
                        message=(
                            "السيشن بتاع لينكدان اتقفلت ومحتاجة موافقة يدوية (كابتشا أو "
                            "تحقق ثنائي) — افتح لينكدان وسجّل دخول يدوي، أو وافق على طلب "
                            "الموافقة اللي وصلك على موبايلك، علشان الفحص الدوري يرجع يشتغل."
                        ),
                        channel="TELEGRAM",
                        priority="HIGH",
                    ),
                )
                await db.commit()
    except Exception:
        logger.exception("linkedin_session_healthcheck_error")


async def recycle_browser():
    """Periodically tears down and lets the shared Playwright browser
    relaunch fresh — added 2026-08-06 after tracing a real, live "AI
    request hangs then times out" incident back to host resource
    starvation, not an AI/timeout bug: `ps` showed a chrome-headless-shell
    renderer process pinned at 66% CPU for 87+ minutes straight with zero
    scans actively running at the time, load average 5.55 on this host's
    ~3 cores, and a trivial 20-token Ollama request timing out at 90s
    purely from CPU contention (confirmed via a direct Ollama benchmark
    run seconds later on the same host: a real generation took 257s, of
    which 75s was just prompt-eval). Every real browser-using call site
    (linkedin/baaeed/sabbar providers, post_scanner.py) already closes its
    own context correctly in a `finally` block — this isn't an
    application-level leak of Playwright objects, it's Chromium's own
    renderer-process pooling keeping OS processes warm for reuse
    indefinitely on a long-lived browser instance, which a resource-
    constrained shared host can't comfortably absorb over many hours of
    accumulated scan/discovery activity. browser_manager.close() saves
    every named context's session state (see save_state() in
    browser/playwright/manager.py) before tearing down, so the LinkedIn
    login isn't lost — the next call to launch() just starts a clean
    browser and restores it from disk, same as it already does across a
    normal container restart."""
    from smarthunt.browser.playwright.manager import browser_manager

    if not browser_manager.is_running:
        return

    try:
        await browser_manager.close()
        logger.info("browser_recycle_completed")
    except Exception:
        logger.exception("browser_recycle_failed")


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
    from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate
    from smarthunt.scheduler.history.service import scheduler_history_service

    async with AsyncSessionLocal() as db:
        try:
            posts = await scan_home_feed()
            saved = await linkedin_monitor_service.scan_and_save(db, posts)
            logger.info(
                "scheduled_linkedin_feed_scan_completed",
                extra={"scanned": len(posts), "saved": len(saved)},
            )
            await scheduler_history_service.create(
                db,
                SchedulerHistoryCreate(
                    provider=LINKEDIN_FEED_PROVIDER,
                    status="completed",
                    jobs_found=len(saved),
                    message=f"scanned={len(posts)} saved={len(saved)}",
                ),
            )
            await db.commit()
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
    from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate
    from smarthunt.scheduler.history.service import scheduler_history_service

    async with AsyncSessionLocal() as db:
        accounts = await linkedin_monitor_service.list_accounts(db)

    total_scanned = 0
    total_saved = 0

    for account in accounts:
        if not account.enabled:
            continue

        async with AsyncSessionLocal() as db:
            try:
                posts = await scan_profile_posts(account.profile_url)
                saved = await linkedin_monitor_service.scan_and_save(db, posts)
                await linkedin_monitor_service.mark_account_checked(db, account.id)
                total_scanned += len(posts)
                total_saved += len(saved)
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

    async with AsyncSessionLocal() as db:
        await scheduler_history_service.create(
            db,
            SchedulerHistoryCreate(
                provider=LINKEDIN_ACCOUNTS_PROVIDER,
                status="completed",
                jobs_found=total_saved,
                message=f"accounts={len(accounts)} scanned={total_scanned} saved={total_saved}",
            ),
        )
        await db.commit()


async def scan_hashtags_daily():
    """Once a day, scans the first ~50 posts under every *enabled*
    hashtag in the owner's DB-backed hashtag list (linkedin_monitor
    MonitoredHashtag — moved 2026-08-06 from a hardcoded Python list so
    each hashtag can be added/removed/enabled from the job-search page,
    the same as monitored accounts) for job-relevant content — the
    automatic counterpart to each hashtag's own "افحص دلوقتي" button. One
    hashtag failing (navigation error, etc.) doesn't skip the rest of the
    list."""
    from smarthunt.linkedin_monitor import service as linkedin_monitor_service
    from smarthunt.linkedin_monitor.post_scanner import scan_hashtag_posts
    from smarthunt.scheduler.history.schemas import SchedulerHistoryCreate
    from smarthunt.scheduler.history.service import scheduler_history_service

    async with AsyncSessionLocal() as db:
        hashtags = await linkedin_monitor_service.list_hashtags(db)

    total_scanned = 0
    total_saved = 0
    scanned_count = 0

    for hashtag in hashtags:
        if not hashtag.enabled:
            continue

        scanned_count += 1
        async with AsyncSessionLocal() as db:
            try:
                posts = await scan_hashtag_posts(hashtag.tag)
                saved = await linkedin_monitor_service.scan_and_save(db, posts)
                await linkedin_monitor_service.mark_hashtag_checked(db, hashtag.id)
                total_scanned += len(posts)
                total_saved += len(saved)
                logger.info(
                    "scheduled_hashtag_scan_completed",
                    extra={"hashtag": hashtag.tag, "scanned": len(posts), "saved": len(saved)},
                )
            except Exception:
                logger.exception("scheduled_hashtag_scan_failed", extra={"hashtag": hashtag.tag})
                continue

    async with AsyncSessionLocal() as db:
        await scheduler_history_service.create(
            db,
            SchedulerHistoryCreate(
                provider=LINKEDIN_HASHTAGS_PROVIDER,
                status="completed",
                jobs_found=total_saved,
                message=f"hashtags={scanned_count} scanned={total_scanned} saved={total_saved}",
            ),
        )
        await db.commit()
