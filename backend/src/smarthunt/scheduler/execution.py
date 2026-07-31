from contextlib import asynccontextmanager
from time import perf_counter

from smarthunt.metrics.scheduler_execution import (
    scheduler_execution_duration_seconds,
    scheduler_execution_failed_total,
    scheduler_execution_total,
)


@asynccontextmanager
async def track_scheduler_execution(
    job_name: str,
):

    start = perf_counter()

    scheduler_execution_total.labels(
        job=job_name
    ).inc()

    try:
        yield

    except Exception:
        scheduler_execution_failed_total.labels(
            job=job_name
        ).inc()
        raise

    finally:
        duration = perf_counter() - start

        scheduler_execution_duration_seconds.labels(
            job=job_name
        ).observe(duration)
