from dataclasses import dataclass


@dataclass(slots=True)
class ProviderExecution:
    provider: str
    success: bool
    jobs: list
    error: str | None = None
    duration: float = 0.0
