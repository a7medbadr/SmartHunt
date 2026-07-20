import pytest
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from smarthunt.browser.playwright.retry import (
    CaptchaDetectedError,
    ExponentialBackoff,
    RetryExecutor,
    RetryPolicy,
)


@pytest.fixture
def fast_policy() -> RetryPolicy:
    return RetryPolicy(
        max_attempts=3,
        base_delay=0.01,
        max_delay=0.02,
        multiplier=2.0,
        jitter=0.0,
    )


@pytest.mark.asyncio
async def test_retry_success_after_transient_failure(fast_policy):
    executor = RetryExecutor(policy=fast_policy)

    calls = {"count": 0}

    async def flaky():
        calls["count"] += 1

        if calls["count"] < 2:
            raise PlaywrightTimeoutError("Navigation timeout")

        return "ok"

    result = await executor.run(
        flaky,
        operation="goto",
        provider="linkedin",
        page_url="https://example.com",
    )

    assert result == "ok"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_retry_exhausted_raises_last_exception(fast_policy):
    executor = RetryExecutor(policy=fast_policy)

    calls = {"count": 0}

    async def always_fails():
        calls["count"] += 1
        raise PlaywrightTimeoutError("Navigation timeout")

    with pytest.raises(PlaywrightTimeoutError):
        await executor.run(
            always_fails,
            operation="click",
            provider="linkedin",
            page_url="https://example.com",
        )

    assert calls["count"] == fast_policy.max_attempts


@pytest.mark.asyncio
async def test_retryable_exception_is_retried(fast_policy):
    executor = RetryExecutor(policy=fast_policy)

    calls = {"count": 0}

    async def detached_locator():
        calls["count"] += 1

        if calls["count"] < 2:
            raise Exception("Locator detached from document")

        return "recovered"

    result = await executor.run(
        detached_locator,
        operation="fill",
        provider="linkedin",
        page_url="https://example.com",
    )

    assert result == "recovered"
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_non_retryable_custom_exception_raises_immediately(fast_policy):
    executor = RetryExecutor(policy=fast_policy)

    calls = {"count": 0}

    async def captcha():
        calls["count"] += 1
        raise CaptchaDetectedError("CAPTCHA detected on page")

    with pytest.raises(CaptchaDetectedError):
        await executor.run(
            captcha,
            operation="click",
            provider="linkedin",
            page_url="https://example.com",
        )

    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_non_retryable_message_pattern_raises_immediately(fast_policy):
    executor = RetryExecutor(policy=fast_policy)

    calls = {"count": 0}

    async def invalid_credentials():
        calls["count"] += 1
        raise Exception("Invalid credentials provided")

    with pytest.raises(Exception):
        await executor.run(
            invalid_credentials,
            operation="fill",
            provider="linkedin",
            page_url="https://example.com",
        )

    assert calls["count"] == 1


def test_exponential_backoff_increases_with_attempts():
    policy = RetryPolicy(
        base_delay=1.0,
        max_delay=10.0,
        multiplier=2.0,
        jitter=0.0,
    )

    backoff = ExponentialBackoff(policy)

    assert backoff.delay_for_attempt(1) == pytest.approx(1.0)
    assert backoff.delay_for_attempt(2) == pytest.approx(2.0)
    assert backoff.delay_for_attempt(3) == pytest.approx(4.0)


def test_exponential_backoff_respects_max_delay():
    policy = RetryPolicy(
        base_delay=1.0,
        max_delay=3.0,
        multiplier=2.0,
        jitter=0.0,
    )

    backoff = ExponentialBackoff(policy)

    assert backoff.delay_for_attempt(5) == pytest.approx(3.0)
