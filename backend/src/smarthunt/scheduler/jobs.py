import logging

from smarthunt.database.session import AsyncSessionLocal
from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job_service import failed_scheduler_job_service

logger = logging.getLogger("smarthunt.scheduler")


async def _run_scheduled_discovery(topic: str, query: str) -> None:
    """Run a real discovery pass for `query` across every provider and
    persist results, tracking success/failure via the same
    scheduler_history / failed_scheduler_job tables the Scheduler page
    reads from."""
    provider_label = f"scheduler:{topic}"

    async with AsyncSessionLocal() as db:
        try:
            result = await DiscoveryService(db).discover(query=query, provider=provider_label)
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


async def discover_python():
    await _run_scheduled_discovery("python", "python developer")


async def discover_linux():
    await _run_scheduled_discovery("linux", "linux administrator")


async def discover_devops():
    await _run_scheduled_discovery("devops", "devops engineer")
