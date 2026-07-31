import asyncio

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
from smarthunt.core.config import settings
from smarthunt.logging.logger import logger


class AIService:

    def __init__(
        self,
        provider: AIProvider | None = None,
        retries: int | None = None,
        fallback_provider: AIProvider | None = AIProvider.LOCAL,
    ):

        self.provider = (
            provider
            or AIProvider(settings.ai_provider)
        )

        self.retries = (
            retries
            if retries is not None
            else settings.ai_max_retries
        )

        self.fallback_provider = fallback_provider


    async def _execute(
        self,
        provider_name: AIProvider,
        request: AIRequest,
    ) -> AIResponse:

        provider = AIProviderFactory.get(
            provider_name
        )

        return await asyncio.wait_for(
            provider.generate(request),
            timeout=request.timeout,
        )


    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        if not settings.enable_ai_services:
            raise AIProviderError(
                "AI services are disabled"
            )


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

                logger.info(
                    "AI generation started provider=%s attempt=%s",
                    provider,
                    attempt,
                )

                response = await self._execute(
                    provider,
                    request,
                )

                logger.info(
                    "AI generation completed provider=%s",
                    provider,
                )

                return response


            except asyncio.TimeoutError as exc:

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
                "AI provider failed provider=%s attempt=%s error=%s",
                provider,
                attempt,
                last_exception,
            )


        if (
            self.fallback_provider
            and self.fallback_provider != provider
        ):

            logger.warning(
                "Trying AI fallback provider=%s",
                self.fallback_provider,
            )

            try:

                return await self._execute(
                    self.fallback_provider,
                    request,
                )

            except Exception as exc:

                raise AIRetryExceededError(
                    f"Fallback failed: {exc}"
                ) from exc


        raise AIRetryExceededError(
            f"AI retries exhausted: {last_exception}"
        )


ai_service = AIService()
