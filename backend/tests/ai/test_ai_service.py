import pytest

from smarthunt.ai.service import AIService
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
)


@pytest.mark.asyncio
async def test_ai_service_local_provider():

    service = AIService(
        provider=AIProvider.LOCAL,
    )

    response = await service.generate(
        AIRequest(
            prompt="test prompt",
        )
    )

    assert response.success is True
    assert response.provider == AIProvider.LOCAL
    assert "test prompt" in response.content
