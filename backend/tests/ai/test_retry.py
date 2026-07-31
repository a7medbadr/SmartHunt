import pytest

from smarthunt.ai.exceptions import AIRetryExceededError
from smarthunt.ai.service import AIService
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
)


@pytest.mark.asyncio
async def test_ai_retry_exhausted():

    service = AIService(
        provider=AIProvider.OPENAI,
        retries=1,
        fallback_provider=None,
    )

    with pytest.raises(AIRetryExceededError):

        await service.generate(
            AIRequest(
                prompt="test",
            )
        )
