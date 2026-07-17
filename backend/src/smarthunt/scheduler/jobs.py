import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from smarthunt.providers.registry import provider_registry

logger = logging.getLogger("smarthunt.scheduler")
scheduler = AsyncIOScheduler()


async def sync_providers_job():
    logger.info("Starting background provider synchronization...")
    try:
        raw_jobs = await provider_registry.fetch_all_jobs_safe()
        logger.info(f"Fetched {len(raw_jobs)} jobs from healthy providers.")
    except Exception as e:
        logger.error(f"Error during scheduled provider sync: {e}")


async def discover_python():
    logger.info("Running Python jobs discovery task...")
    # Add python job search logic here if needed


async def discover_linux():
    logger.info("Running Linux jobs discovery task...")
    # Add linux job search logic here if needed


async def discover_devops():
    logger.info("Running DevOps jobs discovery task...")
    # Add devops job search logic here if needed


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(sync_providers_job, 'interval', minutes=30, id="provider_sync_job")
        scheduler.start()
        logger.info("Provider Scheduler started successfully (30m interval).")
