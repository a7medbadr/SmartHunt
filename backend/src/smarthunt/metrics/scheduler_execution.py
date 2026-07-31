from prometheus_client import Counter, Histogram

scheduler_execution_total = Counter(
    "smarthunt_scheduler_execution_total",
    "Total scheduler job executions",
    ["job"],
)


scheduler_execution_failed_total = Counter(
    "smarthunt_scheduler_execution_failed_total",
    "Total failed scheduler executions",
    ["job"],
)


scheduler_execution_duration_seconds = Histogram(
    "smarthunt_scheduler_execution_duration_seconds",
    "Scheduler job execution duration",
    ["job"],
)


__all__ = [
    "scheduler_execution_total",
    "scheduler_execution_failed_total",
    "scheduler_execution_duration_seconds",
]
