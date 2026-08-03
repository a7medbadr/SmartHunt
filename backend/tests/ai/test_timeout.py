import asyncio

import pytest

from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIRetryExceededError
from smarthunt.ai.factory import AIProviderFactory
from smarthunt.ai.service import AIService
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)


class TimeoutProvider(BaseAIProvider):

    name = AIProvider.LOCAL

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        await asyncio.sleep(1)

        return AIResponse(
            provider=self.name,
            content="timeout",
        )


@pytest.mark.asyncio
async def test_ai_timeout(monkeypatch):
    """AIProviderFactory.register() mutates a module-level cache with no
    built-in undo — calling it directly (as this test used to) leaked a
    broken LOCAL provider (always returns content="timeout") into every
    test running afterward that hits the real LOCAL fallback, e.g. any
    AI-backed feature in a test env with no OpenAI key configured.
    monkeypatch.setitem restores the original registration automatically
    after this test."""

    monkeypatch.setitem(
        AIProviderFactory._providers,
        AIProvider.LOCAL,
        TimeoutProvider(),
    )

    service = AIService(
        provider=AIProvider.LOCAL,
        retries=1,
        fallback_provider=None,
    )

    with pytest.raises(AIRetryExceededError):

        await service.generate(
            AIRequest(
                prompt="test",
                timeout=0.01,
            )
        )
