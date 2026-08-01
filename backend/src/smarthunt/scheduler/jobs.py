import logging

from smarthunt.database.session import AsyncSessionLocal
from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job_service import failed_scheduler_job_service
from smarthunt.scheduler.retry_worker import TOPIC_QUERIES, scheduler_retry_worker

logger = logging.getLogger("smarthunt.scheduler")

# Saudi Arabia only, per the project owner's explicit requirement — see
# CLAUDE.md's "Discovery scope" note before broadening this.
DISCOVERY_LOCATION = "Saudi Arabia"


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
