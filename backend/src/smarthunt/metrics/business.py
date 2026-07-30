from prometheus_client import Counter, Gauge

jobs_created_total = Counter(
    "smarthunt_jobs_created_total",
    "Total jobs persisted",
)

discoveries_total = Counter(
    "smarthunt_discoveries_total",
    "Total discovery executions",
)

users_registered_total = Counter(
    "smarthunt_users_registered_total",
    "Total registered users",
)

notifications_sent_total = Counter(
    "smarthunt_notifications_sent_total",
    "Total notifications sent",
)

notifications_failed_total = Counter(
    "smarthunt_notifications_failed_total",
    "Total notification delivery failures",
)

notifications_unread_total = Gauge(
    "smarthunt_notifications_unread_total",
    "Current unread notifications",
)

__all__ = [
    "jobs_created_total",
    "discoveries_total",
    "users_registered_total",
    "notifications_sent_total",
    "notifications_failed_total",
    "notifications_unread_total",
]
