from smarthunt.metrics.failed_jobs import (
    scheduler_failed_jobs_total,
)
from smarthunt.metrics.scheduler_lock import (
    scheduler_lock_acquired_total,
)


def test_scheduler_metrics_exist():

    assert scheduler_failed_jobs_total is not None
    assert scheduler_lock_acquired_total is not None
