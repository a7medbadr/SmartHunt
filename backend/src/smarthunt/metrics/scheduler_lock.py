from prometheus_client import Counter

scheduler_lock_acquired_total = Counter(
    "scheduler_lock_acquired_total",
    "Total scheduler locks acquired",
)

scheduler_lock_conflicts_total = Counter(
    "scheduler_lock_conflicts_total",
    "Total scheduler lock conflicts",
)

scheduler_lock_expired_total = Counter(
    "scheduler_lock_expired_total",
    "Total expired scheduler locks removed",
)
