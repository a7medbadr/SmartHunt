import logging

from smarthunt.providers.registry import provider_registry
from smarthunt.scheduler.execution import (
    track_scheduler_execution,
)

logger = logging.getLogger("smarthunt.scheduler")


async def sync_providers_job():

    async with track_scheduler_execution("provider_sync"):

        logger.info("Starting provider synchronization")

        raw_jobs = await provider_registry.fetch_all_jobs_safe()

        logger.info(
            "Fetched %s jobs",
            len(raw_jobs),
        )


async def discover_python():

    async with track_scheduler_execution("discover_python"):

        logger.info("Running Python discovery")


async def discover_linux():

    async with track_scheduler_execution("discover_linux"):

        logger.info("Running Linux discovery")


async def discover_devops():

    async with track_scheduler_execution("discover_devops"):

        logger.info("Running DevOps discovery")
