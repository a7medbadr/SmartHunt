import asyncio

import httpx

from smarthunt.ai.base import BaseAIProvider
from smarthunt.ai.exceptions import AIProviderError, AITimeoutError
from smarthunt.ai.types import (
    AIProvider,
    AIRequest,
    AIResponse,
)
from smarthunt.core.config import settings

# The configured local model (see settings.ollama_model) is small and
# CPU-bound — running two generations at once doesn't parallelize, it
# just makes both slower via contention, which was observed live
# 2026-08-03: overlapping requests each individually exceeded their own
# 90s per-attempt timeout and burned through all of ai_max_retries
# before falling back to the (fake) LOCAL provider — the same request
# run alone typically finished in under 30s. Serializing keeps each
# request's full timeout budget meaningful.
_ollama_semaphore = asyncio.Semaphore(1)


class OllamaProvider(BaseAIProvider):

    name = AIProvider.OLLAMA

    async def generate(
        self,
        request: AIRequest,
    ) -> AIResponse:

        if not settings.ollama_url:
            raise AIProviderError("Ollama URL is not configured")

        payload = {
            "model": settings.ollama_model,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }

        try:
            async with _ollama_semaphore:
                async with httpx.AsyncClient(timeout=request.timeout) as client:
                    response = await client.post(
                        f"{settings.ollama_url}/api/generate",
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()

            return AIResponse(
                provider=self.name,
                content=data.get("response", ""),
                success=True,
            )

        except httpx.TimeoutException as exc:
            raise AITimeoutError(f"Ollama request timed out: {exc}") from exc

        except httpx.HTTPError as exc:
            raise AIProviderError(f"Ollama provider failed: {exc}") from exc
