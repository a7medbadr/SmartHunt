import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from smarthunt.discovery.service import DiscoveryService
from smarthunt.scheduler.failed_job import FailedSchedulerJob
from smarthunt.scheduler.failed_job_repository import (
    FailedJobRepository,
)
from smarthunt.scheduler.failed_job_service import (
    failed_scheduler_job_service,
)

# Maps a scheduled discovery job's `job_reference` back to the query it
# should re-run. Owned here (not scheduler/jobs.py) so both that module
# and this one can import it without a circular dependency.
#
# Matches the project owner's actual profile (2026-08-01, explicit
# correction after generic "python developer"/"devops engineer" queries
# were pulling in software-dev/full-stack/network roles they have zero
# interest in) — a Linux/AIX/OpenShift systems & infrastructure
# administrator, not a software developer. Verify against the owner's
# uploaded resume before changing these, don't guess.
#
# "devops" re-added 2026-08-05 — a deliberate, explicit request from the
# owner (not a reversion of the note above): they now want to actively
# target and apply to DevOps roles too, on top of the existing sysadmin
# scope, not instead of it. is_relevant_job_title's own keyword filter
# (matching/services/job_relevance.py) still gates results afterward, so
# this doesn't reopen the original "generic devops query pulls in
# full-stack roles" problem on its own.
TOPIC_QUERIES = {
    "linux": "Linux Administrator",
    "openshift": "OpenShift Administrator",
    "vmware": "VMware Administrator",
    "storage": "Storage Administrator",
    "devops": "DevOps Engineer",
}

# Kept in sync with scheduler/jobs.py's DISCOVERY_LOCATION — Saudi Arabia
# only, per the project owner's explicit requirement.
DISCOVERY_LOCATION = "Saudi Arabia"

# Kept in sync with scheduler/jobs.py's DISCOVERY_CALL_TIMEOUT_SECONDS
# (same circular-import reason as DISCOVERY_LOCATION above) — see that
# constant's own comment for why every discover() call here needs a
# bound: an unbounded hang on one retried job would silently freeze this
# whole 30-minute sweep (and every later FAILED job queued behind it)
# forever, the exact bug this project has now hit on the scheduled
# discovery jobs themselves.
DISCOVERY_CALL_TIMEOUT_SECONDS = 300


class SchedulerRetryWorker:
    """Actually retries FAILED scheduler jobs, up to MAX_RETRIES, instead
    of just flagging them as retry-eligible and leaving them there."""

    def __init__(self):
        self.repository = FailedJobRepository()

    async def process(
        self,
        db: AsyncSession,
    ):
        result = await db.execute(
            select(FailedSchedulerJob).where(FailedSchedulerJob.status == "FAILED")
        )
        failed_jobs = list(result.scalars().all())

        processed = []

        for job in failed_jobs:
            updated = await failed_scheduler_job_service.prepare_retry(db, job)

            if updated.status == "RETRY_PENDING":
                query = TOPIC_QUERIES.get(updated.job_reference)

                if query is None:
                    # Don't know how to re-run this job type — don't get
                    # stuck retrying it forever.
                    updated.status = "FAILED_FINAL"
                    await db.flush()
                else:
                    await failed_scheduler_job_service.mark_running(db, updated)

                    try:
                        await asyncio.wait_for(
                            DiscoveryService(db).discover(
                                query=query,
                                location=DISCOVERY_LOCATION,
                                provider=updated.provider,
                            ),
                            timeout=DISCOVERY_CALL_TIMEOUT_SECONDS,
                        )
                        updated = await failed_scheduler_job_service.mark_success(db, updated)
                    except Exception as exc:
                        updated = await failed_scheduler_job_service.mark_failed(
                            db, updated, str(exc)
                        )

            processed.append(updated)

        return processed


scheduler_retry_worker = SchedulerRetryWorker()
