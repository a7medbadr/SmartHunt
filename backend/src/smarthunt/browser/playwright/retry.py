from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, TypeVar

from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from smarthunt.browser.playwright.manager import browser_manager
from smarthunt.logging.logger import logger

try:
    from prometheus_client import Counter

    playwright_retry_total = Counter(
        "playwright_retry_total",
        "Total number of Playwright retry attempts",
        ["operation", "provider"],
    )

    playwright_retry_success = Counter(
        "playwright_retry_success",
        "Total number of Playwright operations that succeeded after a retry",
        ["operation", "provider"],
    )

    playwright_retry_failed = Counter(
        "playwright_retry_failed",
        "Total number of Playwright operations that failed after exhausting retries",
        ["operation", "provider"],
    )

    _METRICS_ENABLED = True

except ImportError:
    _METRICS_ENABLED = False


T = TypeVar("T")


# Substring patterns matched against the lowercased exception message.
RETRYABLE_MESSAGE_PATTERNS: tuple[str, ...] = (
    "locator detached",
    "element is not attached",
    "execution context destroyed",
    "execution context was destroyed",
    "navigation timeout",
)

NON_RETRYABLE_MESSAGE_PATTERNS: tuple[str, ...] = (
    "captcha detected",
    "mfa required",
    "authentication failed",
    "unsupported form",
    "invalid credentials",
)


class CaptchaDetectedError(Exception):
    """Raised when a CAPTCHA challenge is detected. Never retried."""


class MFARequiredError(Exception):
    """Raised when MFA is required. Never retried."""


class AuthenticationFailedError(Exception):
    """Raised when authentication fails. Never retried."""


class UnsupportedFormError(Exception):
    """Raised when the application form is not supported. Never retried."""


class InvalidCredentialsError(Exception):
    """Raised when provided credentials are invalid. Never retried."""


NON_RETRYABLE_EXCEPTIONS: tuple[type[Exception], ...] = (
    CaptchaDetectedError,
    MFARequiredError,
    AuthenticationFailedError,
    UnsupportedFormError,
    InvalidCredentialsError,
)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 0.5
    max_delay: float = 8.0
    multiplier: float = 2.0
    jitter: float = 0.1


class ExponentialBackoff:
    """
    Computes the delay before a given retry attempt.
    attempt=1 means "delay before the 2nd try".
    """

    def __init__(self, policy: RetryPolicy):
        self.policy = policy

    def delay_for_attempt(self, attempt: int) -> float:
        raw = self.policy.base_delay * (
            self.policy.multiplier ** (attempt - 1)
        )

        capped = min(raw, self.policy.max_delay)

        jitter_amount = capped * self.policy.jitter

        return max(
            0.0,
            capped + random.uniform(-jitter_amount, jitter_amount),
        )


@dataclass
class RetryContext:
    operation: str
    provider: str = "unknown"
    page_url: str = "unknown"
    attempt: int = 0
    elapsed: float = 0.0


@dataclass
class RetryResult:
    success: bool
    result: Any = None
    attempts: int = 0
    last_exception: Optional[BaseException] = None


class RetryExecutor:

    def __init__(self, policy: Optional[RetryPolicy] = None):
        self.policy = policy or RetryPolicy()
        self.backoff = ExponentialBackoff(self.policy)

    @staticmethod
    def _is_non_retryable(exc: BaseException) -> bool:
        if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
            return True

        message = str(exc).lower()

        return any(
            pattern in message
            for pattern in NON_RETRYABLE_MESSAGE_PATTERNS
        )

    @staticmethod
    def _is_retryable(exc: BaseException) -> bool:
        if isinstance(exc, PlaywrightTimeoutError):
            return True

        if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
            return True

        message = str(exc).lower()

        if "target closed" in message:
            # Only worth retrying if the browser itself is still alive.
            return browser_manager.is_running

        return any(
            pattern in message
            for pattern in RETRYABLE_MESSAGE_PATTERNS
        )

    @staticmethod
    def _record_metric(counter, operation: str, provider: str) -> None:
        if _METRICS_ENABLED:
            counter.labels(operation=operation, provider=provider).inc()

    async def run(
        self,
        func: Callable[..., Awaitable[T]],
        *args: Any,
        operation: str = "unknown",
        provider: str = "unknown",
        page_url: str = "unknown",
        **kwargs: Any,
    ) -> T:

        start = time.monotonic()
        last_exception: Optional[BaseException] = None

        for attempt in range(1, self.policy.max_attempts + 1):

            self._record_metric(
                playwright_retry_total, operation, provider
            )

            try:
                result = await func(*args, **kwargs)

                if attempt > 1:
                    self._record_metric(
                        playwright_retry_success, operation, provider
                    )

                    elapsed = time.monotonic() - start

                    logger.info(
                        f"Retry #{attempt} operation={operation} "
                        f"provider={provider} reason=recovered "
                        f"elapsed={elapsed:.2f}s"
                    )

                return result

            except Exception as exc:

                last_exception = exc
                elapsed = time.monotonic() - start

                if self._is_non_retryable(exc):
                    logger.warning(
                        f"NonRetryable operation={operation} "
                        f"provider={provider} page_url={page_url} "
                        f"reason={exc} elapsed={elapsed:.2f}s"
                    )
                    raise

                if not self._is_retryable(exc):
                    logger.warning(
                        f"Unrecognized exception, not retrying "
                        f"operation={operation} provider={provider} "
                        f"page_url={page_url} reason={exc} "
                        f"elapsed={elapsed:.2f}s"
                    )
                    raise

                logger.info(
                    f"Retry #{attempt} operation={operation} "
                    f"provider={provider} page_url={page_url} "
                    f"reason={exc} elapsed={elapsed:.2f}s"
                )

                if attempt >= self.policy.max_attempts:
                    self._record_metric(
                        playwright_retry_failed, operation, provider
                    )
                    break

                await asyncio.sleep(
                    self.backoff.delay_for_attempt(attempt)
                )

        raise last_exception


retry_executor = RetryExecutor()
