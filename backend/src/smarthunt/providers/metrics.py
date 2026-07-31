from prometheus_client import Counter
from prometheus_client import Gauge

provider_failures_total = Counter(
    "provider_failures_total",
    "Total provider failures",
    [
        "provider",
    ],
)

provider_open_circuit = Gauge(
    "provider_open_circuit",
    "Provider circuit breaker state",
    [
        "provider",
    ],
)

provider_recovered_total = Counter(
    "provider_recovered_total",
    "Recovered providers",
    [
        "provider",
    ],
)
