import asyncio
import time

from smarthunt.ai.exceptions import (
    AIProviderError,
    AIRetryExceededError,
    AITimeoutError,
)
from smarthunt.ai.factory import AIProviderFactory
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)
from smarthunt.logging.logger import logger


class AIService:

    def __init__(
        self,
        provider: AIProvider = AIProvider.OPENAI,
        retries: int = 3,
        fallback_provider: AIProvider = AIProvider.LOCAL,
    ):
        self.provider = provider
        self.retries = retries
        self.fallback_provider = fallback_provider


    async def _execute(
        self,
        provider_name: AIProvider,
        request: AIRequest,
        fallback_used: bool = False,
    ) -> AIResponse:

        provider = AIProviderFactory.get(
            provider_name
        )

        start = time.monotonic()

        response = await asyncio.wait_for(
            provider.generate(request),
            timeout=request.timeout,
        )

        response.fallback_used = fallback_used
        response.latency_ms = (
            time.monotonic() - start
        ) * 1000

        return response


    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        provider = (
            request.provider
            or self.provider
        )

        last_exception = None

        for attempt in range(
            1,
            self.retries + 1,
        ):

            try:

                return await self._execute(
                    provider,
                    request,
                )

            except asyncio.TimeoutError:

                last_exception = AITimeoutError(
                    f"Timeout provider={provider}"
                )

            except AIProviderError as exc:

                last_exception = exc

            except Exception as exc:

                last_exception = AIProviderError(
                    str(exc)
                )

            logger.warning(
                "AI failure provider=%s attempt=%s error=%s",
                provider,
                attempt,
                last_exception,
            )


        if (
            self.fallback_provider
            and self.fallback_provider != provider
        ):

            try:

                return await self._execute(
                    self.fallback_provider,
                    request,
                    fallback_used=True,
                )

            except Exception as exc:

                raise AIRetryExceededError(
                    f"Fallback failed: {exc}"
                ) from exc


        raise AIRetryExceededError(
            f"AI retries exhausted: {last_exception}"
        )


ai_service = AIService()
