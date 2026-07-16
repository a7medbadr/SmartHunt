from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

resource = Resource.create(
    {
        "service.name": "smarthunt-backend"
    }
)

provider = TracerProvider(resource=resource)

trace.set_tracer_provider(provider)
