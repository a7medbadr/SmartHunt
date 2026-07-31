import pytest

from smarthunt.ai.health import ai_health_check


@pytest.mark.asyncio
async def test_ai_health_check():

    result = await ai_health_check()

    assert result["status"] in ("healthy", "degraded")

    assert len(result["providers"]) > 0

    assert "provider" in result["providers"][0]


@pytest.mark.asyncio
async def test_ai_health_reflects_real_configuration():
    """Regression test: this used to report every provider as
    available=true unconditionally, regardless of whether it had a key
    configured or was even reachable."""
    result = await ai_health_check()

    by_provider = {p["provider"]: p for p in result["providers"]}

    # In the test environment, no cloud provider keys are configured.
    assert by_provider["openai"]["available"] is False
    assert by_provider["anthropic"]["available"] is False

    # "local" has no external dependency, so it's always available.
    assert by_provider["local"]["available"] is True
