import pytest

from smarthunt.ai.exceptions import AIProviderError
from smarthunt.ai.providers.openai import OpenAIProvider
from smarthunt.ai.types import AIRequest


@pytest.mark.asyncio
async def test_openai_missing_key():

    provider = OpenAIProvider()

    with pytest.raises(AIProviderError):

        await provider.generate(
            AIRequest(
                prompt="test",
            )
        )
