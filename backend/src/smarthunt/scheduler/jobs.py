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

        return {
            "jobs_found": len(raw_jobs),
        }

    except Exception as exc:
        logger.exception(
            "Provider sync failed: %s",
            exc,
        )
        raise


async def discover_python():

    logger.info(
        "Running Python jobs discovery task..."
    )

    return {
        "task": "python",
        "status": "completed",
    }


async def discover_linux():

    logger.info(
        "Running Linux jobs discovery task..."
    )

    return {
        "task": "linux",
        "status": "completed",
    }


async def discover_devops():

    logger.info(
        "Running DevOps jobs discovery task..."
    )

    return {
        "task": "devops",
        "status": "completed",
    }


def start_scheduler():

    if not scheduler.running:

        scheduler.add_job(
            sync_providers_job,
            "interval",
            minutes=30,
            id="provider_sync_job",
            replace_existing=True,
        )

        scheduler.start()

        logger.info(
            "Provider Scheduler started successfully."
        )
