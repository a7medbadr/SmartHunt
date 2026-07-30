from prometheus_client import Counter


events_published_total = Counter(
    "smarthunt_events_published_total",
    "Total published events",
)

events_failed_total = Counter(
    "smarthunt_events_failed_total",
    "Total failed events",
)

events_processed_total = Counter(
    "smarthunt_events_processed_total",
    "Total processed events",
)
