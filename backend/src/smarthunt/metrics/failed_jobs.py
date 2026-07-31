from prometheus_client import Counter

scheduler_failed_jobs_total = Counter(
    "smarthunt_scheduler_failed_jobs_total",
    "Total failed scheduler jobs",
)


scheduler_failed_jobs_retry_total = Counter(
    "smarthunt_scheduler_failed_jobs_retry_total",
    "Total scheduler failed job retries",
)


__all__ = [
    "scheduler_failed_jobs_total",
    "scheduler_failed_jobs_retry_total",
]
