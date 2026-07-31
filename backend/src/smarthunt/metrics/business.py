from prometheus_client import Counter, Gauge


jobs_created_total = Counter(
    "smarthunt_jobs_created_total",
    "Total jobs persisted",
)


jobs_processed_total = Counter(
    "smarthunt_jobs_processed_total",
    "Total jobs processed",
)


discoveries_total = Counter(
    "smarthunt_discoveries_total",
    "Total discovery executions",
)


users_registered_total = Counter(
    "smarthunt_users_registered_total",
    "Total registered users",
)


login_attempts_total = Counter(
    "smarthunt_login_attempts_total",
    "Total login attempts",
)


applications_created_total = Counter(
    "smarthunt_applications_created_total",
    "Total applications created",
)


ai_calls_total = Counter(
    "smarthunt_ai_calls_total",
    "Total AI service calls",
)


api_errors_total = Counter(
    "smarthunt_api_errors_total",
    "Total API errors",
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
    "jobs_processed_total",
    "discoveries_total",
    "users_registered_total",
    "login_attempts_total",
    "applications_created_total",
    "ai_calls_total",
    "api_errors_total",
    "notifications_sent_total",
    "notifications_failed_total",
    "notifications_unread_total",
]
