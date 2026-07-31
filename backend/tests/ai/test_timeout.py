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
async def test_ai_timeout():

    AIProviderFactory.register(
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
