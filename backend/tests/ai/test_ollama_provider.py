from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from smarthunt.ai.exceptions import AIProviderError, AITimeoutError
from smarthunt.ai.providers.ollama import OllamaProvider
from smarthunt.ai.types import AIRequest


@pytest.mark.asyncio
async def test_ollama_generate_calls_real_api():
    """The provider must make an actual HTTP call to Ollama's /api/generate
    and return its response content — not echo the prompt back."""
    provider = OllamaProvider()

    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "real model output"}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client

    with patch("smarthunt.ai.providers.ollama.httpx.AsyncClient", return_value=mock_client):
        result = await provider.generate(AIRequest(prompt="hello"))

    assert result.success is True
    assert result.content == "real model output"
    assert result.content != "hello"

    call_kwargs = mock_client.post.call_args
    assert call_kwargs.args[0].endswith("/api/generate")
    assert call_kwargs.kwargs["json"]["prompt"] == "hello"
    assert call_kwargs.kwargs["json"]["stream"] is False


@pytest.mark.asyncio
async def test_ollama_generate_timeout():
    provider = OllamaProvider()

    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.TimeoutException("timed out")
    mock_client.__aenter__.return_value = mock_client

    with patch("smarthunt.ai.providers.ollama.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AITimeoutError):
            await provider.generate(AIRequest(prompt="hello"))


@pytest.mark.asyncio
async def test_ollama_generate_http_error():
    provider = OllamaProvider()

    mock_client = AsyncMock()
    mock_client.post.side_effect = httpx.ConnectError("connection refused")
    mock_client.__aenter__.return_value = mock_client

    with patch("smarthunt.ai.providers.ollama.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(AIProviderError):
            await provider.generate(AIRequest(prompt="hello"))
