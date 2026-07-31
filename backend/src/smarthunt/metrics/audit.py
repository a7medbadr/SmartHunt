from prometheus_client import Counter

audit_events_total = Counter(
    "smarthunt_audit_events_total",
    "Total audit events created",
)


audit_failures_total = Counter(
    "smarthunt_audit_failures_total",
    "Total audit failures",
)
