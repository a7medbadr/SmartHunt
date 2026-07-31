from datetime import UTC
from datetime import datetime
from datetime import timedelta

from smarthunt.providers.circuit_breaker import (
    CircuitBreaker,
    ProviderState,
)


def test_initial_state():

    cb = CircuitBreaker()

    assert cb.state == ProviderState.CLOSED
    assert cb.failure_count == 0
    assert cb.allow_request() is True


def test_open_after_threshold():

    cb = CircuitBreaker(failure_threshold=3)

    cb.record_failure()
    cb.record_failure()

    assert cb.state == ProviderState.CLOSED

    cb.record_failure()

    assert cb.state == ProviderState.OPEN
    assert cb.allow_request() is False


def test_half_open_after_retry_timeout():

    cb = CircuitBreaker(retry_after_seconds=60)

    cb.record_failure()
    cb.record_failure()
    cb.record_failure()

    cb.last_failure = datetime.now(UTC) - timedelta(seconds=61)

    assert cb.allow_request() is True
    assert cb.state == ProviderState.HALF_OPEN


def test_success_closes_circuit():

    cb = CircuitBreaker(failure_threshold=3)

    cb.record_failure()
    cb.record_failure()
    cb.record_failure()

    cb.record_success()

    assert cb.state == ProviderState.CLOSED
    assert cb.failure_count == 0
    assert cb.allow_request() is True


def test_failure_after_recovery():

    cb = CircuitBreaker(failure_threshold=3)

    cb.record_failure()
    cb.record_failure()
    cb.record_failure()

    cb.record_success()

    cb.record_failure()

    assert cb.state == ProviderState.CLOSED
    assert cb.failure_count == 1
