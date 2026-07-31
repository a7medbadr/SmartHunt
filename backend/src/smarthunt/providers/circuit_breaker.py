from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum


class ProviderState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass(slots=True)
class CircuitBreaker:

    retry_after_seconds: int = 300
    failure_threshold: int = 3

    state: ProviderState = ProviderState.CLOSED
    failure_count: int = 0
    last_failure: datetime | None = None

    def allow_request(self) -> bool:

        if self.state in (
            ProviderState.CLOSED,
            ProviderState.HALF_OPEN,
        ):
            return True

        if self.last_failure is None:
            return True

        if (datetime.now(UTC) - self.last_failure) >= timedelta(seconds=self.retry_after_seconds):
            self.state = ProviderState.HALF_OPEN
            return True

        return False

    def record_success(self) -> None:

        self.failure_count = 0
        self.last_failure = None
        self.state = ProviderState.CLOSED

    def record_failure(self) -> None:

        self.failure_count += 1
        self.last_failure = datetime.now(UTC)

        if self.failure_count >= self.failure_threshold:
            self.state = ProviderState.OPEN
