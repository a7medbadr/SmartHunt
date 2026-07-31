import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from smarthunt.providers.registry import provider_registry


logger = logging.getLogger("smarthunt.scheduler")

scheduler = AsyncIOScheduler()


async def sync_providers_job():

    logger.info(
        "Starting background provider synchronization..."
    )

    try:

        raw_jobs = await provider_registry.fetch_all_jobs_safe()

        logger.info(
            "Fetched %s jobs from healthy providers.",
            len(raw_jobs),
        )

    except Exception as exc:

        logger.exception(
            "Provider sync failed: %s",
            exc,
        )


async def discover_python():

    logger.info(
        "Running Python jobs discovery task..."
    )

    try:
        # Discovery implementation will be connected here
        pass

    except Exception as exc:

        logger.exception(
            "Python discovery failed: %s",
            exc,
        )


async def discover_linux():

    logger.info(
        "Running Linux jobs discovery task..."
    )

    try:
        pass

    except Exception as exc:

        logger.exception(
            "Linux discovery failed: %s",
            exc,
        )


async def discover_devops():

    logger.info(
        "Running DevOps jobs discovery task..."
    )

    try:
        pass

    except Exception as exc:

        logger.exception(
            "DevOps discovery failed: %s",
            exc,
        )


def start_scheduler():

    if not scheduler.running:

        scheduler.add_job(
            sync_providers_job,
            "interval",
            minutes=30,
            id="provider_sync_job",
        )

        scheduler.start()

        logger.info(
            "Provider Scheduler started successfully."
        )
