from prometheus_client import Counter

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
