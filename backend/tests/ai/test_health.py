import pytest

from smarthunt.ai.health import ai_health_check


@pytest.mark.asyncio
async def test_ai_health_check():

    result = await ai_health_check()

    assert result["status"] == "healthy"

    assert len(
        result["providers"]
    ) > 0

    assert "provider" in result["providers"][0]
