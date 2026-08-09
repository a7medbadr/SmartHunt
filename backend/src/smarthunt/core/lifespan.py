from contextlib import asynccontextmanager

from fastapi import FastAPI

from smarthunt.database.health import check_database_health
from smarthunt.database.migration import run_migrations
from smarthunt.database.session import close_engine
from smarthunt.logging.config import configure_logging
from smarthunt.scheduler.scheduler import scheduler
from smarthunt.services.scheduler_service import SchedulerService

import structlog

logger = structlog.get_logger("smarthunt")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    logger.info(
        "application_startup",
        service="smarthunt-backend",
    )

    try:
        await run_migrations()

        logger.info(
            "database_migration_completed",
            service="smarthunt-backend",
        )

    except Exception:
        logger.exception(
            "database_migration_failed",
            service="smarthunt-backend",
        )
        raise

    try:
        await check_database_health()

        logger.info(
            "database_health_check_passed",
            service="smarthunt-backend",
        )

    except Exception:
        logger.exception(
            "database_health_check_failed",
            service="smarthunt-backend",
        )
        raise

    try:
        SchedulerService().start()

    except Exception:
        # A scheduler that fails to start shouldn't take the whole API
        # down — discovery/retry automation just won't run until fixed.
        logger.exception(
            "scheduler_start_failed_at_startup",
            service="smarthunt-backend",
        )

    try:
        await SchedulerService().catch_up_scheduled_jobs()

    except Exception:
        # A missed catch-up just means the regular trigger runs at its
        # next scheduled time as usual — not worth failing startup over.
        logger.exception(
            "scheduled_job_catchup_failed_at_startup",
            service="smarthunt-backend",
        )

    yield

    logger.info(
        "application_shutdown",
        service="smarthunt-backend",
    )

    # Found live 2026-08-08: a real WhatsApp QR login succeeded (session
    # live in the shared "whatsapp" browser context), but a routine
    # backend restart moments later — before any explicit save_state()
    # call had a reason to fire — silently discarded it, forcing a second
    # real QR scan. BrowserManager.close() already exists specifically as
    # a safety net for this ("capture whatever session state exists right
    # now for every named context, so an unplanned shutdown doesn't lose
    # a session that was never explicitly saved" — see its own docstring)
    # but nothing here ever actually called it, so every provider's
    # session (LinkedIn included) was exposed to the same risk, not just
    # WhatsApp's newer login flow. Safe to call unconditionally — a no-op
    # when the browser was never launched this run.
    try:
        from smarthunt.browser.playwright.manager import browser_manager

        await browser_manager.close()
    except Exception:
        logger.exception(
            "browser_manager_close_failed_at_shutdown",
            service="smarthunt-backend",
        )

    if scheduler.running:
        scheduler.shutdown(wait=False)

    await close_engine()

    logger.info(
        "database_connection_closed",
        service="smarthunt-backend",
    )
