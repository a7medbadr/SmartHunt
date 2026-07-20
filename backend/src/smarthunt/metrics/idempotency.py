from prometheus_client import Counter

idempotency_hits_total = Counter(
    "idempotency_hits_total",
    "Existing idempotency keys reused",
)

idempotency_created_total = Counter(
    "idempotency_created_total",
    "New idempotency keys created",
)

duplicate_requests_prevented_total = Counter(
    "duplicate_requests_prevented_total",
    "Duplicate apply requests prevented",
)
